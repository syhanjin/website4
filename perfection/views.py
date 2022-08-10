# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-8-10 11:28                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import io
import random

from django.conf import settings as django_settings
from django.http import FileResponse
from django.utils import timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BalancedColumns, PageBreak, Paragraph, SimpleDocTemplate
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from images.models import Image
from perfection.models.base import PerfectionStudent
from perfection.serializers.base import (
    PerfectionStudentCreateSerializer, PerfectionStudentSerializer,
    PerfectionStudentWordLibrariesSetSerializer,
)
from .conf import settings
from .models.words import WordLibrary, WordsPerfection
from .serializers.words import (
    WordLibrarySerializer, WordsPerfectionFinishSerializer, WordsPerfectionRememberAndReviewSerializer,
    WordsPerfectionRememberSerializer,
    WordsPerfectionReviewSerializer,
    WordsPerfectionSerializer, WordsPerfectionUnrememberedSerializer,
)

# pdf 生成格式
pdfmetrics.registerFont(TTFont('霞鹜文楷', django_settings.BASE_DIR / 'perfection/fonts/LXGWWenKai-Regular_0.ttf'))
pdfmetrics.registerFont(TTFont('Consolas', django_settings.BASE_DIR / 'perfection/fonts/consola.ttf'))
pdfmetrics.registerFont(TTFont('ConsolaBd', django_settings.BASE_DIR / 'perfection/fonts/consolab.ttf'))
pdfmetrics.registerFont(TTFont('ConsolaIt', django_settings.BASE_DIR / 'perfection/fonts/consolai.ttf'))
pdfmetrics.registerFont(TTFont('ConsolaBI', django_settings.BASE_DIR / 'perfection/fonts/consolaz.ttf'))
pdfmetrics.registerFontFamily(
    "Consolas", normal="Consolas", bold="ConsolaBd", italic="ConsolaIt", boldItalic="ConsolaBI"
)

STYLESHEET = getSampleStyleSheet()

LINE_STYLE = STYLESHEET['Normal']
LINE_STYLE.spaceAfter = 12
TITLE_STYLE = STYLESHEET['Title']
TITLE_STYLE.spaceAfter = 15


class PDF_TEMPLATES:
    class REMEMBER:
        BODY_HEADER = '<para><font face="霞鹜文楷" size=18>{date}【记忆版】</font></para>'
        BODY_HEADER_STYLE = TITLE_STYLE

        LINE = '<para>' \
               '<font face="Consolas" size=16>{index}. {symbol} <b>{word}</b> </font>' \
               '<font face="霞鹜文楷" size=16>{chinese}</font>' \
               '<br/></para>'
        LINE_STYLE = LINE_STYLE

        BODY_FOOTER = ''
        BODY_FOOTER_STYLE = STYLESHEET['Normal']

    class REVIEW:
        BODY_HEADER = '<para><font face="霞鹜文楷" size=18>{date}【打卡版】</font></para>'
        BODY_HEADER_STYLE = TITLE_STYLE

        LINE = '<para>' \
               '<font face="Consolas" size=12>{index}. {word} ____________________</font>' \
               '<br/></para>'
        LINE_STYLE = LINE_STYLE

        BODY_FOOTER = ''
        BODY_FOOTER_STYLE = STYLESHEET['Normal']


def to_pdf(words, date, mode="review"):
    template = getattr(PDF_TEMPLATES, mode.upper(), None)
    if template is None:
        raise ValueError(f"mode={mode}, template={template}")
    story = [
        Paragraph(template.BODY_HEADER.format(date=date), template.BODY_HEADER_STYLE)
    ]
    body = []
    for index, word in enumerate(words):
        body.append(
            Paragraph(
                template.LINE.format(
                    index=index + 1,
                    word=word.word.word,
                    symbol=word.word.symbol,
                    chinese=word.word.chinese
                ), template.LINE_STYLE
            )
        )
    if mode.lower() == 'review':
        story.append(BalancedColumns(body, nCols=2))
        story.append(PageBreak())
        for index, word in enumerate(words):
            story.append(
                Paragraph(
                    PDF_TEMPLATES.REMEMBER.LINE.format(
                        index=index + 1,
                        word=word.word.word,
                        symbol=word.word.symbol,
                        chinese=word.word.chinese
                    ), PDF_TEMPLATES.REMEMBER.LINE_STYLE
                )
            )

    else:
        story += body
    story.append(Paragraph(template.BODY_FOOTER, template.BODY_FOOTER_STYLE))
    file = io.BytesIO()
    doc = SimpleDocTemplate(
        file,
        topMargin=1.27 * cm, bottomMargin=1.27 * cm,
        leftMargin=1.27 * cm, rightMargin=1.27 * cm
    )
    doc.build(story)
    return file


def to_pdf_resp(words, created, mode):
    mode2text = {'review': '打卡版', 'remember': '记忆版'}
    date = created.__format__("%Y-%m-%d")
    pdf = to_pdf(words=words, date=date, mode=mode)
    pdf.seek(0)
    resp = FileResponse(pdf, as_attachment=True, filename=f"""{date}【{mode2text[mode]}】.pdf""")
    resp.headers["Access-Control-Expose-Headers"] = 'Content-Disposition'
    return resp


"""
def to_word(words, mode="review"):
    if isinstance(words, QuerySet):
        words = list(words)
    if mode == 'review':
        random.shuffle(words)
    fontsize = 12
    doc = Document()
    doc.styles['Normal'].font.name = 'Consolas'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    doc.styles['Normal'].font.size = Pt(fontsize)
    if mode == 'review':
        doc.sections[0]._sectPr.xpath('./w:cols')[0].set(qn('w:num'), '2')
    doc.sections[0].top_margin = Cm(1.27)
    doc.sections[0].bottom_margin = Cm(1.27)
    doc.sections[0].left_margin = Cm(1.27)
    doc.sections[0].right_margin = Cm(1.27)
    for index, word in enumerate(words):
        if mode == 'review':
            para = doc.add_paragraph()
            para.add_run('%d. ' % (index + 1))
            para.add_run(word.word.word + ' ')
            para.add_run("_" * 15)
            para.paragraph_format.line_spacing = 1.5
        elif mode == 'remember':
            para = doc.add_paragraph()
            para.add_run('%d. ' % (index + 1))
            para.add_run(word.word.symbol + ' ')
            para.add_run(word.word.word + ' ').bold = True
            para.add_run(word.word.chinese)
            para.paragraph_format.line_spacing = 1.2
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
    if mode == 'review':
        # 加入答案
        doc.add_section()
        doc.sections[1]._sectPr.xpath('./w:cols')[0].set(qn('w:num'), '1')
        for index, word in enumerate(words):
            para = doc.add_paragraph()
            para.add_run('%d. ' % (index + 1))
            para.add_run(word.word.symbol + ' ')
            para.add_run(word.word.word + ' ').bold = True
            para.add_run(word.word.chinese)
            para.paragraph_format.line_spacing = 1.2
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
    return doc


# 生成word文档，该函数并未封装
def to_word_response(words, created, mode="review"):
    doc = to_word(words, mode)
    response = HttpResponse(content_type="application/octet-stream")
    response["Content-Disposition"] = \
        f'''attachment; filename={created.__format__("%Y-%m-%d-remember")}.docx'''.encode()
    response["Access-Control-Expose-Headers"] = "Content-Disposition"
    doc.save(response)
    return response
"""


class PerfectionStudentViewSet(viewsets.ModelViewSet):
    serializer_class = PerfectionStudentSerializer
    queryset = PerfectionStudent.objects.all()
    permission_classes = settings.PERMISSIONS.student
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if self.action == "list" and user.admin == 0:
            queryset = queryset.filter(pk=user.perfection.pk)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PerfectionStudentCreateSerializer
        elif self.action == 'set_words_library':
            return PerfectionStudentWordLibrariesSetSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.student_create
        elif self.action == 'set_words_library':
            self.permission_classes = settings.PERMISSIONS.words_library_set
        elif self.action == "me":
            self.permission_classes = settings.PERMISSIONS.student
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    def create(self, request, *args, **kwargs):
        # 测试通过-正常
        user = self.get_instance()
        if getattr(user, 'perfection', None) is not None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'perfection': ['已开通打卡功能']})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfection = serializer.save()
        perfection.user = user
        perfection.word_libraries.set(
            WordLibrary.objects.filter(is_default__in=[True])
        )
        perfection.save()
        return Response(status=status.HTTP_200_OK, data={'perfection_id': perfection.id})

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        _object = self.get_instance().perfection
        serializer = self.get_serializer(_object)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def set_words_library(self, request, *args, **kwargs):
        _object = self.get_instance().perfection
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        libraries = WordLibrary.objects.filter(id__in=serializer.validated_data['word_libraries'])
        _object.word_libraries.set(libraries)
        _object.save()
        return Response(
            status=status.HTTP_200_OK,
            data={'word_libraries': list(_object.word_libraries.all().values_list('name', flat=True))}
        )


class WordsPagination(PageNumberPagination):
    # 默认的大小
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 30


class WordsPerfectionViewSet(viewsets.ModelViewSet):
    serializer_class = WordsPerfectionSerializer
    queryset = WordsPerfection.objects.all()
    permission_classes = settings.PERMISSIONS.words
    lookup_field = 'id'
    pagination_class = WordsPagination

    def get_queryset(self):
        user = self.request.user
        # if user.admin > 0 or user.perfection.role == 'teacher':
        #     queryset = super().get_queryset()
        # else:
        queryset = user.perfection.words.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'remember' or self.action == 'remember_file':
            return WordsPerfectionRememberSerializer
        elif self.action == 'review' or self.action == 'review_file':
            return WordsPerfectionReviewSerializer
        elif self.action == 'unremembered':
            return WordsPerfectionUnrememberedSerializer
        elif self.action == 'remember_review':
            return WordsPerfectionRememberAndReviewSerializer
        elif self.action == 'finish':
            return WordsPerfectionFinishSerializer
        # elif self.action == 'libraries':
        #     return WordLibraryAllSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.words_create
        # elif self.action == 'libraries':
        #     self.permission_classes = settings.PERMISSIONS.word_libraries
        elif (self.action == 'remember' or self.action == 'review'
              or self.action == 'remember_file' or self.action == 'review_file'
              or self.action == 'remember_review' or self.action == 'unremembered'):
            self.permission_classes = settings.PERMISSIONS.words
        elif self.action == 'finish':
            self.permission_classes = settings.PERMISSIONS.words_finish
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(methods=['get', 'post'], detail=True)
    def remember(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        if not request.query_params.get('detail'):
            data['remember'] = [x['word'] for x in data['remember']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def unremembered(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        if not request.query_params.get('detail'):
            data['unremembered'] = [x['word'] for x in data['unremembered']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def review(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        if not request.query_params.get('detail'):
            data['review'] = [x['word'] for x in data['review']]
            if request.query_params.get('simple'):
                data['review'] = [x['word'] for x in data['review']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def remember_file(self, request, *args, **kwargs):
        instance = self.get_object()
        return to_pdf_resp(instance.remember.all(), instance.created, mode='remember')

    @action(methods=['get'], detail=True)
    def review_file(self, request, *args, **kwargs):
        instance = self.get_object()
        words = list(instance.review.all())
        random.shuffle(words)
        return to_pdf_resp(words, instance.created, mode='review')

    @action(methods=['get'], detail=True)
    def remember_review(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        if not request.query_params.get('detail'):
            data['remember'] = [x['word'] for x in data['remember']]
            data['review'] = [x['word'] for x in data['review']]
        return Response(data=data, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=False)
    # def libraries(self, request, *args, **kwargs):
    #     serializer = self.get_serializer()
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        _object = self.get_object()
        if _object.is_finished:
            # 伪造drf验证返回值
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['打卡已完成']})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        errors = {}
        review = _object.review.all()
        if review.count() != len(data["review"].keys()):
            errors['review'] = "「打卡版」词量不匹配"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        # 查验传入字典的单词
        review_errors = set(data['review']) - set(review.values_list('word__word', flat=True))
        if len(review_errors) > 0:
            errors['review'] = f"{review_errors} 不是本次「打卡版」的单词"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        _object.update_words(
            review=data['review']
        )
        # _object.picture = data['picture']
        # 处理图片问题
        for pic in data['picture']:
            image = Image.objects.create(image=pic)
            _object.picture.add(image)
        #
        _object.is_finished = True
        _object.finished = timezone.now()
        _object.save()
        picture = []
        for pic in _object.picture.all():
            picture.append(request.build_absolute_uri(pic.image.url))
        return Response(
            status=status.HTTP_200_OK, data={
                "accuracy": _object.accuracy,
                "total": _object.total,
                "picture": picture,
                "unremembered_words": _object.unremembered_words.values_list('word__word', 'word__chinese')
            }
        )


class WordLibraryViewSet(viewsets.ModelViewSet):
    serializer_class = WordLibrarySerializer
    queryset = WordLibrary.objects.all()
    permission_classes = settings.PERMISSIONS.word_libraries
    lookup_field = 'id'
