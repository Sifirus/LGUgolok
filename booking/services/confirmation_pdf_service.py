from io import BytesIO
from xml.sax.saxutils import escape as xml_escape
import os
import logging

from django.urls import reverse
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class BookingConfirmationPdfService:
    FONT_REGULAR = 'Arial'
    FONT_BOLD = 'Arial-Bold'
    _fonts_registered = False

    @classmethod
    def _register_fonts(cls):
        if cls._fonts_registered:
            return

        candidates_regular = [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/ARIAL.TTF',
            'C:\\Windows\\Fonts\\arial.ttf',
        ]
        candidates_bold = [
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/ARIALBD.TTF',
            'C:/Windows/Fonts/arialb.ttf',
            'C:\\Windows\\Fonts\\arialbd.ttf',
        ]

        regular_path = next((p for p in candidates_regular if os.path.exists(p)), None)
        bold_path = next((p for p in candidates_bold if os.path.exists(p)), None)

        if not regular_path or not bold_path:
            logger.warning("Arial not found, trying Times New Roman")
            regular_path = next((p for p in [
                'C:/Windows/Fonts/times.ttf', 'C:/Windows/Fonts/TIMES.TTF',
            ] if os.path.exists(p)), None)
            bold_path = next((p for p in [
                'C:/Windows/Fonts/timesbd.ttf', 'C:/Windows/Fonts/TIMESBD.TTF',
            ] if os.path.exists(p)), None)

        if not regular_path or not bold_path:
            fonts_dir = 'C:/Windows/Fonts'
            if os.path.exists(fonts_dir):
                available = [f for f in os.listdir(fonts_dir) if f.lower().endswith('.ttf')][:10]
                raise RuntimeError(f"Не найден шрифт с кириллицей. Доступные TTF: {available}")
            raise RuntimeError("Папка C:/Windows/Fonts не найдена.")

        pdfmetrics.registerFont(TTFont(cls.FONT_REGULAR, regular_path))
        pdfmetrics.registerFont(TTFont(cls.FONT_BOLD, bold_path))
        cls._fonts_registered = True

    @staticmethod
    def _escape_text(value):
        return xml_escape(str(value or '')).replace('\n', '<br/>')

    @staticmethod
    def _format_person(user):
        profile = getattr(user, 'profile', None)
        if not profile:
            return 'Не указано', 'Не указано'
        parts = [
            getattr(profile, 'last_name', '') or '',
            getattr(profile, 'first_name', '') or '',
            getattr(profile, 'second_name', '') or '',
        ]
        fio = ' '.join(p for p in parts if p).strip() or 'Не указано'
        department = getattr(profile, 'department', '') or 'Не указано'
        return fio, department

    @staticmethod
    def _format_dt(dt_obj):
        if not dt_obj:
            return 'Не указано'
        return timezone.localtime(dt_obj).strftime('%d.%m.%Y %H:%M')

    @staticmethod
    def _format_date(date_obj):
        if not date_obj:
            return 'Не указано'
        return date_obj.strftime('%d.%m.%Y')

    @staticmethod
    def _format_time_range(booking):
        if not booking.event_date or not booking.event_start_time or not booking.event_end_time:
            return 'Не указано'
        return (
            f"{booking.event_date.strftime('%d.%m.%Y')} "
            f"{booking.event_start_time.strftime('%H:%M')} - "
            f"{booking.event_end_time.strftime('%H:%M')}"
        )

    @classmethod
    def build_pdf(cls, booking, request):
        cls._register_fonts()

        approval = getattr(booking, 'approval', None)

        auto_approved = booking.status == booking.Status.APPROVED and approval is None
        manual_approved = (
                approval is not None
                and booking.status == booking.Status.APPROVED
                and approval.decision == 'approved'
        )
        if not (auto_approved or manual_approved):
            raise PermissionError('Подтверждение доступно только для согласованных заявок')

        booking_url = request.build_absolute_uri(reverse('booking_detail', args=[booking.pk]))
        now_str = timezone.localtime(timezone.now()).strftime('%d.%m.%Y %H:%M')

        dispatcher_fio, dispatcher_department = cls._format_person(booking.initiator)

        if auto_approved:
            approver_fio = 'Автоматически'
            approver_department = '—'
            approved_at_str = now_str
        else:
            approver_fio, approver_department = cls._format_person(approval.approver)
            approved_at_str = cls._format_dt(approval.decided_at)

        equipment_items = list(booking.equipment.all()) if hasattr(booking, 'equipment') else []
        equipment_text = ', '.join(str(eq) for eq in equipment_items) if equipment_items else 'Нет'

        signed = booking.signed
        signed_source = booking.signature_source

        group_rows = []
        if booking.group_id:
            group_rows = [
                ('Идентификатор группы', f'#{booking.group_id}'),
                ('Название группы', booking.group.title or 'Не указано'),
                ('Период группы',
                 f"{cls._format_date(booking.group.date_from)} - {cls._format_date(booking.group.date_to)}"),
                ('Всего подзаявок', str(booking.group.total_count)),
            ]

        detail_rows = [
            ('Идентификатор заявки в системе', f'#{booking.pk}'),
            ('Дата формирования документа', now_str),
            ('Сведения о диспетчере', dispatcher_fio),
            ('Отдел диспетчера', dispatcher_department),
            ('Дата и время бронирования', cls._format_time_range(booking)),
            ('Тип мероприятия', booking.get_event_type_display()),
            ('Первичный комментарий', booking.comment or 'Нет'),
            ('Аудитория', f"{booking.room.name}, вместимость {booking.room.capacity}"),
            ('Заявленное количество участников', str(booking.participants)),
            ('Список оборудования', equipment_text),
            ('Вид согласования', 'Автоматическое' if auto_approved else 'Ручное'),
            ('Сведения о согласующем', approver_fio),
            ('Отдел согласующего', approver_department),
            ('Дата согласования заявки', approved_at_str),
        ]

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ConfirmationTitle', parent=styles['Title'],
            fontName=cls.FONT_BOLD, fontSize=18, leading=22,
            alignment=TA_LEFT, spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            'ConfirmationSubtitle', parent=styles['Normal'],
            fontName=cls.FONT_REGULAR, fontSize=9, leading=12,
            textColor=colors.HexColor('#5B6472'), spaceAfter=10,
        )
        section_style = ParagraphStyle(
            'ConfirmationSection', parent=styles['Heading2'],
            fontName=cls.FONT_BOLD, fontSize=11, leading=14,
            textColor=colors.HexColor('#1F3C88'), spaceBefore=8, spaceAfter=6,
        )
        cell_label_style = ParagraphStyle(
            'ConfirmationCellLabel', parent=styles['Normal'],
            fontName=cls.FONT_BOLD, fontSize=8.8, leading=11,
            textColor=colors.HexColor('#233041'),
        )
        cell_value_style = ParagraphStyle(
            'ConfirmationCellValue', parent=styles['Normal'],
            fontName=cls.FONT_REGULAR, fontSize=8.8, leading=11,
            textColor=colors.HexColor('#233041'),
        )
        cell_auto_style = ParagraphStyle(
            'ConfirmationCellAuto', parent=styles['Normal'],
            fontName=cls.FONT_BOLD, fontSize=8.8, leading=11,
            textColor=colors.HexColor('#D97706'),
        )
        small_note_style = ParagraphStyle(
            'ConfirmationSmallNote', parent=styles['Normal'],
            fontName=cls.FONT_REGULAR, fontSize=8, leading=10,
            textColor=colors.HexColor('#5B6472'),
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=16 * mm, rightMargin=16 * mm,
            topMargin=16 * mm, bottomMargin=16 * mm,
            title=f'Подтверждение бронирования #{booking.pk}',
            subject='Подтверждение бронирования',
        )

        story = []
        story.append(Paragraph('Подтверждение бронирования', title_style))

        header_lines = [f"Заявка #{booking.pk}"]
        if booking.group_id:
            header_lines.append(f"Группа #{booking.group_id}")
        header_lines.append(f"Ссылка на заявку: {booking_url}")

        story.append(Paragraph(
            '<br/>'.join(cls._escape_text(line) for line in header_lines),
            subtitle_style,
        ))
        story.append(Spacer(1, 3 * mm))

        if group_rows:
            story.append(Paragraph('Сведения о группе', section_style))
            group_table_data = [
                [Paragraph(cls._escape_text(l), cell_label_style),
                 Paragraph(cls._escape_text(v), cell_value_style)]
                for l, v in group_rows
            ]
            group_table = Table(group_table_data, colWidths=[56 * mm, 118 * mm], hAlign='LEFT')
            group_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7F9FC')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9E1EC')),
                ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D9E1EC')),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(group_table)
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph('Реквизиты подтверждения', section_style))

        AUTO_LABELS = {'Вид согласования', 'Сведения о согласующем', 'Отдел согласующего', 'Дата согласования заявки'}

        detail_table_data = []
        for label, value in detail_rows:
            val_style = cell_auto_style if (auto_approved and label in AUTO_LABELS) else cell_value_style
            detail_table_data.append([
                Paragraph(cls._escape_text(label), cell_label_style),
                Paragraph(cls._escape_text(value), val_style),
            ])

        detail_table = Table(detail_table_data, colWidths=[64 * mm, 110 * mm], hAlign='LEFT')
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#D9E1EC')),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D9E1EC')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7),
            ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 4 * mm))

        story.append(Paragraph('QR-код для проверки заявки в системе', section_style))
        qr_drawing = createBarcodeDrawing(
            'QR', value=booking_url, barLevel='M',
            width=34 * mm, height=34 * mm,
        )
        qr_table = Table(
            [[
                Paragraph(cls._escape_text(
                    'Откройте ссылку или отсканируйте QR-код для перехода к заявке в системе.'
                ), small_note_style),
                qr_drawing,
            ]],
            colWidths=[137 * mm, 38 * mm], hAlign='LEFT',
        )
        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9E1EC')),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(qr_table)

        story.append(Paragraph('Реквизиты подписи и печати', section_style))

        if signed:
            if signed_source == booking.SignatureSource.SYSTEM:
                signature_data = [
                    [Paragraph(cls._escape_text('Статус'), cell_label_style),
                     Paragraph(cls._escape_text('Подписано системой'), cell_value_style)],
                    [Paragraph(cls._escape_text('Дата подписи'), cell_label_style),
                     Paragraph(cls._escape_text(cls._format_dt(booking.signed_at)), cell_value_style)],
                    [Paragraph(cls._escape_text('Печать'), cell_label_style),
                     Paragraph(cls._escape_text('Место для печати'), cell_value_style)],
                ]
            else:
                signer_name, signer_department = cls._format_person(booking.signed_by)
                signature_data = [
                    [Paragraph(cls._escape_text('Статус'), cell_label_style),
                     Paragraph(cls._escape_text('Документ подписан'), cell_value_style)],
                    [Paragraph(cls._escape_text('Отметил подписанным'), cell_label_style),
                     Paragraph(cls._escape_text(signer_name), cell_value_style)],
                    [Paragraph(cls._escape_text('Отдел'), cell_label_style),
                     Paragraph(cls._escape_text(signer_department), cell_value_style)],
                    [Paragraph(cls._escape_text('Дата отметки о подписании'), cell_label_style),
                     Paragraph(cls._escape_text(cls._format_dt(booking.signed_at)), cell_value_style)],
                ]
        else:
            signature_data = [
                [Paragraph(cls._escape_text('Подпись'), cell_label_style),
                 Paragraph(cls._escape_text('________________________'), cell_value_style)],
                [Paragraph(cls._escape_text('ФИО'), cell_label_style),
                 Paragraph(cls._escape_text('________________________'), cell_value_style)],
                [Paragraph(cls._escape_text('Дата'), cell_label_style),
                 Paragraph(cls._escape_text('________________________'), cell_value_style)],
                [Paragraph(cls._escape_text('Печать'), cell_label_style),
                 Paragraph(cls._escape_text(''), cell_value_style)],
            ]

        signature_table = Table(signature_data, colWidths=[45 * mm, 129 * mm], hAlign='LEFT')
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7F9FC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9E1EC')),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D9E1EC')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7),
            ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(signature_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        filename_parts = [f'booking_{booking.pk}']
        if booking.group_id:
            filename_parts.append(f'group_{booking.group_id}')
        filename = 'confirmation_' + '_'.join(filename_parts) + '.pdf'

        return pdf_bytes, filename
