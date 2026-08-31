from io import BytesIO

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

class ReportsPdfService:
    FONT_REGULAR = "DejaVuSans"
    FONT_BOLD = "DejaVuSans-Bold"
    _fonts_registered = False

    @classmethod
    def _register_fonts(cls):
        if cls._fonts_registered:
            return

        regular_path = font_manager.findfont(
            font_manager.FontProperties(family="DejaVu Sans", weight="normal")
        )
        bold_path = font_manager.findfont(
            font_manager.FontProperties(family="DejaVu Sans", weight="bold")
        )

        pdfmetrics.registerFont(TTFont(cls.FONT_REGULAR, regular_path))
        pdfmetrics.registerFont(TTFont(cls.FONT_BOLD, bold_path))
        cls._fonts_registered = True

    @staticmethod
    def _escape(value):
        text = "" if value is None else str(value)
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
        )

    @staticmethod
    def _fig_to_image(fig, width=7.0, height=3.2):
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=width * inch, height=height * inch)

    @staticmethod
    def _add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVuSans", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawRightString(
            A4[0] - 16 * mm,
            10 * mm,
            f"Стр. {doc.page}",
        )
        canvas.restoreState()

    @classmethod
    def _build_kpi_table(cls, rows):
        styles = getSampleStyleSheet()
        label_style = ParagraphStyle(
            "kpi_label",
            parent=styles["Normal"],
            fontName=cls.FONT_REGULAR,
            fontSize=9,
            textColor=colors.HexColor("#6B7280"),
            leading=11,
        )
        value_style = ParagraphStyle(
            "kpi_value",
            parent=styles["Normal"],
            fontName=cls.FONT_BOLD,
            fontSize=14,
            textColor=colors.HexColor("#111827"),
            leading=16,
        )

        data = []
        for i in range(0, len(rows), 2):
            left = rows[i]
            right = rows[i + 1] if i + 1 < len(rows) else ("", "")
            data.append([
                Paragraph(cls._escape(left[0]), label_style),
                Paragraph(cls._escape(left[1]), value_style),
                Paragraph(cls._escape(right[0]), label_style),
                Paragraph(cls._escape(right[1]), value_style),
            ])

        table = Table(data, colWidths=[34 * mm, 48 * mm, 34 * mm, 48 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E1EA")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return table

    @classmethod
    def _build_trend_chart(cls, labels, values, title):
        fig, ax = plt.subplots(figsize=(10, 3.2))
        ax.plot(labels, values)
        ax.set_title(title)
        ax.set_ylabel("Часы")
        ax.grid(True, alpha=0.25)
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        return cls._fig_to_image(fig, width=7.2, height=2.8)

    @classmethod
    def _build_bar_chart(cls, labels, values, title):
        fig, ax = plt.subplots(figsize=(10, 3.0))
        ax.bar(labels, values)
        ax.set_title(title)
        ax.set_ylabel("Часы")
        ax.grid(True, axis="y", alpha=0.25)
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        return cls._fig_to_image(fig, width=7.2, height=2.6)

    @classmethod
    def _build_capacity_chart(cls, labels, participants, capacity, title):
        fig, ax = plt.subplots(figsize=(10, 3.2))

        ax.bar(labels, participants, label="Участники")
        ax.plot(labels, [capacity] * len(labels), label="Вместимость", color="red")

        ax.set_title(title)
        ax.set_ylabel("Человек")
        ax.grid(True, axis="y", alpha=0.25)
        ax.tick_params(axis="x", rotation=45)
        ax.legend()

        fig.tight_layout()
        return cls._fig_to_image(fig, width=7.2, height=2.8)

    @classmethod
    def _build_pie_chart(cls, labels, values, title):
        fig, ax = plt.subplots(figsize=(8, 3.6))
        if not values or sum(values) == 0:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
            ax.axis("off")
        else:
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
        ax.set_title(title)
        fig.tight_layout()
        return cls._fig_to_image(fig, width=6.8, height=3.0)

    @classmethod
    def _build_heatmap(cls, matrix, days, hours, title):
        fig, ax = plt.subplots(figsize=(10, 4.6))
        im = ax.imshow(matrix, aspect="auto")
        ax.set_title(title)
        ax.set_yticks(range(len(days)))
        ax.set_yticklabels(days)
        ax.set_xticks(range(len(hours)))
        ax.set_xticklabels([str(h) for h in hours], rotation=45)
        fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
        fig.tight_layout()
        return cls._fig_to_image(fig, width=7.2, height=3.7)

    @classmethod
    def build_pdf(cls, report_type, mode, data, date_from, date_to):
        cls._register_fonts()

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title",
            parent=styles["Title"],
            fontName=cls.FONT_BOLD,
            fontSize=18,
            leading=22,
            alignment=TA_LEFT,
            spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        )
        subtitle_style = ParagraphStyle(
            "subtitle",
            parent=styles["Normal"],
            fontName=cls.FONT_REGULAR,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=8,
        )
        section_style = ParagraphStyle(
            "section",
            parent=styles["Heading2"],
            fontName=cls.FONT_BOLD,
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
            textColor=colors.HexColor("#1F3C88"),
        )
        cell_head = ParagraphStyle(
            "cell_head",
            parent=styles["Normal"],
            fontName=cls.FONT_BOLD,
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#111827"),
        )
        cell_body = ParagraphStyle(
            "cell_body",
            parent=styles["Normal"],
            fontName=cls.FONT_REGULAR,
            fontSize=8.2,
            leading=10,
            textColor=colors.HexColor("#111827"),
        )

        buffer = BytesIO()
        filename = f"report_{report_type}_{mode}_{date_from}_{date_to}.pdf"

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Отчёт",
            subject="PDF отчёт",
        )

        story = []
        title = "Отчёт по аудиториям" if report_type == "rooms" else "Отчёт по оборудованию"
        if mode == "resource":
            title = f"{title}, детализация по объекту"

        story.append(Paragraph(title, title_style))
        story.append(Paragraph(
            f"Период: {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}",
            subtitle_style,
        ))
        story.append(Spacer(1, 3 * mm))

        if mode == "overview":
            story.append(Paragraph("Сводные показатели", section_style))
            if report_type == "rooms":
                kpi_rows = [
                    ("Часов занятости", f"{data.get('total_hours', 0)}"),
                    ("Заявок", f"{data.get('total_bookings', 0)}"),
                    ("Средняя загрузка", f"{data.get('avg_load', 0)}%"),
                    ("Отменённых", f"{data.get('canceled_count', 0)}"),
                    ("Доля отмен", f"{data.get('canceled_pct', 0)}%"),
                    ("Пиковый день", data.get("peak_day", "")),
                ]
            else:
                kpi_rows = [
                    ("Часов занятости", f"{data.get('total_hours', 0)}"),
                    ("Заявок", f"{data.get('total_bookings', 0)}"),
                    ("Средняя загрузка", f"{data.get('avg_load', 0)}%"),
                    ("Отменённых", f"{data.get('canceled_count', 0)}"),
                    ("Доля отмен", f"{data.get('canceled_pct', 0)}%"),
                    ("Пиковый день", data.get("peak_day", "")),
                ]

            story.append(cls._build_kpi_table(kpi_rows))
            story.append(Spacer(1, 4 * mm))

            story.append(Paragraph("Графики", section_style))
            trend = cls._build_trend_chart(
                data.get("trend_labels", []),
                data.get("trend_values", []),
                "Тренд загрузки по дням",
            )
            pie = cls._build_pie_chart(
                data.get("pie_labels", []),
                data.get("pie_hours_values", []) or data.get("pie_values", []),
                "Распределение по типам мероприятий",
            )
            heatmap = cls._build_heatmap(
                data.get("heatmap", []),
                data.get("heatmap_days", []),
                data.get("heatmap_hours", []),
                "Тепловая карта, день недели x час",
            )
            hour_dist = cls._build_bar_chart(
                [f"{h:02d}" for h in data.get("heatmap_hours", list(range(24)))],
                data.get("hour_distribution", []),
                "Распределение часов заявок по часам дня",
            )

            story.append(trend)
            story.append(Spacer(1, 4 * mm))
            story.append(pie)
            story.append(Spacer(1, 4 * mm))
            story.append(heatmap)
            story.append(Spacer(1, 4 * mm))
            story.append(hour_dist)
            story.append(Spacer(1, 4 * mm))

            story.append(Paragraph("Список ресурсов", section_style))

            if report_type == "rooms":
                headers = ["Аудитория", "Корпус", "Этаж", "Тип", "Статус", "Заявок", "Отмен", "Часы", "Загрузка %", "Пиковый день"]
                fields = ["name", "building", "floor", "type", "status", "bookings_count", "canceled_count", "total_hours", "load_pct", "peak_day"]
            else:
                headers = ["Наименование", "Модель", "Инв. №", "Тип", "Статус", "Аудитория", "Заявок", "Отмен", "Часы", "Загрузка %", "Пиковый день"]
                fields = ["name", "model", "inventory_number", "type", "status", "room", "bookings_count", "canceled_count", "total_hours", "load_pct", "peak_day"]

            table_data = [[Paragraph(cls._escape(h), cell_head) for h in headers]]
            for item in data.get("items", []):
                table_data.append([
                    Paragraph(cls._escape(item.get(f, "")), cell_body) for f in fields
                ])

            tbl = Table(table_data, repeatRows=1, colWidths=[22 * mm, 20 * mm, 18 * mm, 16 * mm, 18 * mm, 24 * mm, 14 * mm, 14 * mm, 14 * mm, 16 * mm, 20 * mm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E1EA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(tbl)

        else:
            resource = data.get("resource", {})
            summary = data.get("summary", {})

            story.append(Paragraph("Сведения об объекте", section_style))
            meta_rows = [
                ("ID", f"#{resource.get('id', '')}"),
                ("Название", resource.get("name", "")),
                ("Тип", resource.get("type", "")),
                ("Статус", resource.get("status", "")),
                ("Корпус / аудитория", f"{resource.get('building', '')} {resource.get('floor', '')}".strip() if resource.get("kind") == "rooms" else resource.get("room", "")),
            ]
            if resource.get("kind") == "equipment":
                meta_rows.insert(4, ("Инвентарный номер", resource.get("inventory_number", "")))
                meta_rows.append(("Модель", resource.get("model", "")))

            meta_table = Table([
                [Paragraph(cls._escape(a), cell_head), Paragraph(cls._escape(b), cell_body)]
                for a, b in meta_rows
            ], colWidths=[55 * mm, 115 * mm], hAlign="LEFT")
            meta_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E1EA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 4 * mm))

            story.append(Paragraph("Сводные показатели", section_style))
            kpi_rows = [
                ("Часов занятости", f"{summary.get('total_hours', 0)}"),
                ("Заявок", f"{summary.get('total_bookings', 0)}"),
                ("Загрузка", f"{summary.get('load_pct', 0)}%"),
                ("Отменённых", f"{summary.get('canceled_count', 0)}"),
                ("Доля отмен", f"{summary.get('canceled_pct', 0)}%"),
                ("Пиковый день", summary.get("peak_day", "")),
            ]
            story.append(cls._build_kpi_table(kpi_rows))
            story.append(Spacer(1, 4 * mm))

            story.append(Paragraph("Графики", section_style))
            story.append(cls._build_trend_chart(
                data.get("trend_labels", []),
                data.get("trend_values", []),
                "Почасовая занятость по дням",
            ))
            story.append(Spacer(1, 4 * mm))
            story.append(cls._build_pie_chart(
                data.get("pie_labels", []),
                data.get("pie_hours_values", []) or data.get("pie_values", []),
                "Распределение по типам мероприятий",
            ))
            story.append(Spacer(1, 4 * mm))
            story.append(cls._build_heatmap(
                data.get("heatmap", []),
                data.get("heatmap_days", []),
                data.get("heatmap_hours", []),
                "Тепловая карта, день недели x час",
            ))
            story.append(Spacer(1, 4 * mm))
            story.append(cls._build_bar_chart(
                data.get("hour_labels", [f"{h:02d}" for h in range(24)]),
                data.get("hour_values", []),
                "Распределение часов заявок по часам дня",
            ))
            story.append(Spacer(1, 4 * mm))

            if mode == "resource" and report_type == "rooms":
                story.append(cls._build_capacity_chart(
                    [x['label'] for x in data.get('capacity_compare', [])],
                    [x['participants'] for x in data.get('capacity_compare', [])],
                    data.get('resource', {}).get('capacity', 0),
                    "Загрузка аудитории относительно вместимости",
                ))
                story.append(Spacer(1, 4 * mm))

            story.append(Paragraph("Детальная занятость", section_style))
            detail_headers = ["Дата", "Начало", "Конец", "Тип", "Участники", "Статус", "Часы", "До начала", "Комментарий"]
            detail_rows = [[Paragraph(cls._escape(h), cell_head) for h in detail_headers]]
            for row in data.get("detail_rows", []):
                detail_rows.append([
                    Paragraph(cls._escape(row.get("date", "")), cell_body),
                    Paragraph(cls._escape(row.get("start", "")), cell_body),
                    Paragraph(cls._escape(row.get("end", "")), cell_body),
                    Paragraph(cls._escape(row.get("event_type", "")), cell_body),
                    Paragraph(cls._escape(row.get("participants", "")), cell_body),
                    Paragraph(cls._escape(row.get("status", "")), cell_body),
                    Paragraph(cls._escape(row.get("hours", "")), cell_body),
                    Paragraph(cls._escape(row.get("remaining_to_start_hours", "")), cell_body),
                    Paragraph(cls._escape(row.get("comment", "")), cell_body),
                ])

            detail_tbl = Table(detail_rows, repeatRows=1, colWidths=[18 * mm, 15 * mm, 15 * mm, 28 * mm, 14 * mm, 20 * mm, 12 * mm, 18 * mm, 38 * mm])
            detail_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FF")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E1EA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(detail_tbl)

        doc.build(story, onFirstPage=cls._add_page_number, onLaterPages=cls._add_page_number)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if mode == "overview":
            filename = f"{'rooms' if report_type == 'rooms' else 'equipment'}_report_{date_from}_{date_to}.pdf"
        else:
            filename = f"{'rooms' if report_type == 'rooms' else 'equipment'}_resource_{date_from}_{date_to}.pdf"

        return pdf_bytes, filename