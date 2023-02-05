# -*- coding: utf-8 -*-

# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-2-5 12:35                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : build_word_pdf.py                                                 =
#    @Program: website                                                         =
# ==============================================================================
import io

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import BalancedColumns, PageBreak, Paragraph, SimpleDocTemplate

STYLESHEET = getSampleStyleSheet()

REVIEW_LINE_STYLE = STYLESHEET['Normal']
REVIEW_LINE_STYLE.spaceAfter = 12
TITLE_STYLE = STYLESHEET['Title']
TITLE_STYLE.spaceAfter = 15


class PDF_TEMPLATES:
    class REMEMBER:
        BODY_HEADER = '<para><font face="霞鹜文楷" size=18>{date}【记忆版】</font></para>'
        BODY_HEADER_STYLE = TITLE_STYLE

        LINE = '<para spaceAfter=0 spaceBefore=0 leading=12>' \
               '<font face="Consolas" size=12>{index}. {symbol} <b>{word}</b> </font>' \
               '<font face="霞鹜文楷" size=12>{chinese}</font>' \
               '<br/></para>'
        LINE_STYLE = STYLESHEET['Normal']

        BODY_FOOTER = ''
        BODY_FOOTER_STYLE = STYLESHEET['Normal']

    class REVIEW:
        BODY_HEADER = '<para><font face="霞鹜文楷" size=18>{date}【打卡版】</font></para>'
        BODY_HEADER_STYLE = TITLE_STYLE

        LINE = '<para>' \
               '<font face="Consolas" size=12>{index}. {word} _______________</font>' \
               '<br/></para>'
        LINE_STYLE = REVIEW_LINE_STYLE

        NO_WORDS = '<para><font face="霞鹜文楷">今天没有单词</font></para>'
        NO_WORDS_STYLE = STYLESHEET['Normal']

        ADDITION_HEADER = '<para><font face="霞鹜文楷" size=16>附加题</font></para>'
        ADDITION_HEADER_STYLE = TITLE_STYLE

        ADDITION_ANSWER_HEADER = '<para>附加题答案</para>'
        ADDITION_ANSWER_HEADER_STYLE = STYLESHEET['Normal']

        BODY_FOOTER = ''
        BODY_FOOTER_STYLE = STYLESHEET['Normal']


def to_pdf(words, date, addition=None, mode="review"):
    def build_remember():
        story = [
            Paragraph(PDF_TEMPLATES.REMEMBER.BODY_HEADER.format(date=date), PDF_TEMPLATES.REMEMBER.BODY_HEADER_STYLE)
        ]
        body_remember = []
        body_test = []
        for index, word in enumerate(words):
            body_remember.append(
                Paragraph(
                    PDF_TEMPLATES.REMEMBER.LINE.format(
                        index=index + 1,
                        word=word.word.word,
                        symbol=word.word.symbol,
                        chinese=word.word.chinese
                    ), PDF_TEMPLATES.REMEMBER.LINE_STYLE
                )
            )
            body_test.append(
                Paragraph(
                    PDF_TEMPLATES.REVIEW.LINE.format(
                        index=index + 1,
                        word=word.word.word,
                        symbol=word.word.symbol,
                        chinese=word.word.chinese
                    ), PDF_TEMPLATES.REVIEW.LINE_STYLE
                )
            )
        story += body_remember
        story.append(BalancedColumns(body_test, nCols=2))
        story.append(Paragraph(PDF_TEMPLATES.REMEMBER.BODY_FOOTER, PDF_TEMPLATES.REMEMBER.BODY_FOOTER_STYLE))
        return story

    def build_review():
        def build_review_word_line(words_):
            test, answer = [], []
            for index, word in enumerate(words_):
                test.append(
                    Paragraph(
                        PDF_TEMPLATES.REVIEW.LINE.format(
                            index=index + 1,
                            word=word.word.word,
                            symbol=word.word.symbol,
                            chinese=word.word.chinese
                        ), PDF_TEMPLATES.REVIEW.LINE_STYLE
                    )
                )
                answer.append(
                    Paragraph(
                        PDF_TEMPLATES.REMEMBER.LINE.format(
                            index=index + 1,
                            word=word.word.word,
                            symbol=word.word.symbol,
                            chinese=word.word.chinese
                        ), PDF_TEMPLATES.REMEMBER.LINE_STYLE
                    )
                )
            return test, answer

        story = [
            Paragraph(PDF_TEMPLATES.REVIEW.BODY_HEADER.format(date=date), PDF_TEMPLATES.REVIEW.BODY_HEADER_STYLE)
        ]
        words_length = len(words)
        if words_length:
            body_test, body_answer = build_review_word_line(words)
            story.append(BalancedColumns(body_test, nCols=2))
        else:
            body_answer = None
            story.append(Paragraph(PDF_TEMPLATES.REVIEW.NO_WORDS, PDF_TEMPLATES.REVIEW.NO_WORDS_STYLE))
        addition_test, addition_answer = build_review_word_line(addition)
        story.append(Paragraph(PDF_TEMPLATES.REVIEW.ADDITION_HEADER, PDF_TEMPLATES.REVIEW.ADDITION_HEADER_STYLE))
        story.append(BalancedColumns(addition_test, nCols=2))
        story.append(PageBreak())
        if words_length:
            story += body_answer
        story.append(
            Paragraph(PDF_TEMPLATES.REVIEW.ADDITION_ANSWER_HEADER, PDF_TEMPLATES.REVIEW.ADDITION_ANSWER_HEADER_STYLE)
        )
        story += addition_answer
        story.append(Paragraph(PDF_TEMPLATES.REVIEW.BODY_FOOTER, PDF_TEMPLATES.REVIEW.BODY_FOOTER_STYLE))
        return story

    mode = mode.upper()
    if mode == 'REMEMBER':
        story = build_remember()
    elif mode == 'REVIEW':
        story = build_review()
    else:
        raise ValueError(f'mode={mode} is not allowed.')
    file = io.BytesIO()
    doc = SimpleDocTemplate(
        file,
        topMargin=1.27 * cm, bottomMargin=1.27 * cm,
        leftMargin=1.27 * cm, rightMargin=1.27 * cm
    )
    doc.build(story)
    return file
