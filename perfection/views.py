# ==============================================================================
#  Copyright (C) 2022 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2022-10-2 12:54                                                   =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import io
import json
import random
from datetime import datetime, time, timedelta
from urllib.parse import quote

import numpy as np
from django.conf import settings as django_settings
from django.http import FileResponse
from django.utils import timezone
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BalancedColumns, PageBreak, Paragraph, SimpleDocTemplate
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from getui.models import NotificationMessageOffline, NotificationMessageOnline
from getui.servers.push import to_single_alias
from images.models import Image
from perfection.models.base import PerfectionStudent
from perfection.serializers.base import (
    PerfectionStudentCreateSerializer, PerfectionStudentSerializer,
    PerfectionStudentWordLibrariesSetSerializer,
)
from .conf import settings
from .models.class_ import PerfectionClass, PerfectionClassStudent, PerfectionSubject
from .models.teacher import PerfectionTeacher
from .models.words import WordLibrary, WordsPerfection
from .serializers.class_ import (
    PerfectionClassCreateSerializer, PerfectionClassDetailSerializer, PerfectionClassSerializer,
    PerfectionClassStudentInfoSerializer, PerfectionClassStudentSerializer, PerfectionClassStudentUpdateSerializer,
    PerfectionClassSubjectCheckSerializer,
    PerfectionClassSubjectGetSerializer,
    PerfectionSubjectCreateSerializer,
    PerfectionSubjectSerializer,
)
from .serializers.teacher import (
    PerfectionTeacherCreateSerializer,
    PerfectionTeacherSerializer,
)
from .serializers.words import (
    WordLibrarySerializer, WordsPerfectionFinishSerializer, WordsPerfectionListSerializer,
    WordsPerfectionRememberAndReviewSerializer,
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
        return Response(data={'perfection_id': perfection.id})

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
            data={'word_libraries': list(_object.word_libraries.all().values_list('name', flat=True))}
        )


class PerfectionTeacherViewSet(viewsets.ModelViewSet):
    serializer_class = PerfectionTeacherSerializer
    queryset = PerfectionTeacher.objects.all()
    permission_classes = settings.PERMISSIONS.teacher
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if self.action == "list" and user.admin == 0:
            queryset = queryset.filter(pk=user.perfection.pk)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PerfectionTeacherCreateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.teacher_create
        return super().get_permissions()

    def get_instance(self):
        return self.request.user


class ClassPagination(PageNumberPagination):
    # 默认的大小
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 30


class PerfectionClassViewSet(viewsets.ModelViewSet):
    serializer_class = PerfectionClassDetailSerializer
    queryset = PerfectionClass.objects.all()
    permission_classes = settings.PERMISSIONS.class_
    lookup_field = 'id'
    pagination_class = ClassPagination

    def get_queryset(self):
        if self.action == 'add':
            return super().get_queryset()  # .values_list('perfection_class', flat=True)
        user = self.request.user
        if user.perfection.role == 'teacher':
            return user.perfection.classes.all()
        return PerfectionClass.objects.filter(students__perfection=user.perfection_student)

    def get_serializer_class(self):
        if self.action == 'create':
            return PerfectionClassCreateSerializer
        elif self.action == 'list':
            return PerfectionClassSerializer
        # elif self.action == 'students':
        #     return PerfectionClassStudentSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.class_create
        elif self.action == 'add':
            self.permission_classes = settings.PERMISSIONS.class_add
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        class_ = PerfectionClass.objects.create(name=data['name'])
        class_.subject.set(PerfectionSubject.objects.filter(id__in=data['subject']))
        class_.teacher = user.perfection_teacher
        class_.save()
        return Response(
            data={
                "name": class_.name,
                "id": class_.id,
                "subject": list(class_.subject.all().values_list('name', flat=True))
            }
        )

    @action(methods=['get'], detail=True)
    def add(self, request, *args, **kwargs):
        user = request.user
        class_ = self.get_object()
        if class_.students.filter(perfection=user.perfection_student).count() > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['已在班级内']})
        if user.perfection_student.classes.count() > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['由于某些原因，学生暂时只允许加入一个班级']})
        # class_.students.add(user.perfection_student)
        # class_.save()
        PerfectionClassStudent.objects.create(perfection_class=class_, perfection=user.perfection)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(methods=['get'], detail=True)
    # def students(self, request, *args, **kwargs):
    #     _object = self.get_object()
    #     serializer = self.get_serializer(
    #         PerfectionClassStudent.objects.filter(c=_object), many=True
    #     )
    #     return Response(data=serializer.data)


class PerfectionClassStudentViewSet(viewsets.ModelViewSet):
    serializer_class = PerfectionClassStudentSerializer
    queryset = PerfectionClassStudent.objects.all()
    permission_classes = settings.PERMISSIONS.class_
    lookup_field = 'perfection__id'

    def get_queryset(self):
        # print(self.kwargs)
        return self.get_class().students.all()

    def get_class(self):
        return PerfectionClass.objects.get(pk=self.kwargs['class_id'])

    def get_serializer_class(self):
        if self.action == 'set':
            return PerfectionClassStudentUpdateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'set':
            self.permission_classes = settings.PERMISSIONS.student_update
        return super().get_permissions()

    @action(methods=['post'], detail=True)
    def set(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfectionClassSubjectViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PerfectionSubjectSerializer
    queryset = PerfectionSubject.objects.all()
    permission_classes = settings.PERMISSIONS.class_subject
    lookup_field = 'id'

    def get_queryset(self):
        # print(self.kwargs)
        return self.get_class().subject.all()

    def get_serializer_class(self):
        if self.action == 'check':
            return PerfectionClassSubjectCheckSerializer
        elif self.action == 'get_one':
            return PerfectionClassSubjectGetSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['days', 'list_day', 'check', 'get_one']:
            self.permission_classes = settings.PERMISSIONS.class_subject_manage
        return super().get_permissions()

    def get_class(self):
        return PerfectionClass.objects.get(pk=self.kwargs['class_id'])

    def get_qs(self, subject):
        return getattr(settings.MODELS, f'{subject.id}_perfection').objects.filter(
            perfection__in=self.get_class().students.all().values_list('perfection', flat=True)
        )

    def get_qs_date(self, subject, date):
        return self.get_qs(subject).filter(
            created__range=[  # 唉，这是没办法的事
                datetime.combine(date, time(0, 0, 0)),
                datetime.combine(date, time(23, 59, 59, 999))
            ]
        )

    @action(methods=['get'], detail=True)
    def days(self, request, *args, **kwargs):
        page = int(request.query_params.get('page', 1))
        page_size = 20
        subject = self.get_object()
        date = timezone.now().date() - timedelta(days=(page - 1) * page_size)
        cnt, data = 0, []
        class_ = self.get_class()
        while cnt < page_size:
            if date < class_.created.date():
                break
            day = {
                "date": date,
            }
            qs = self.get_qs_date(subject, date)
            date -= timedelta(days=1)
            day["total"] = qs.count()
            if day["total"] == 0:
                continue
            # day["finished"] = qs.filter(is_finished__in=[True]).count()
            # day["checked"] = qs.filter(is_checked__in=[True]).count()
            # 主要是上面的数据库过滤不掉（似乎Djongo对boolean的过滤有问题）
            day["finished"] = np.array(qs.values_list('is_finished', flat=True)).sum()
            day["checked"] = np.array(qs.values_list('is_checked', flat=True)).sum()
            data.append(day)
            cnt += 1
        return Response(
            data={
                "count": len(data),
                "next": date >= class_.created.date(),
                "results": data
            }
        )

    @action(methods=['get'], detail=True)
    def list_day(self, request, *args, **kwargs):
        date = datetime.strptime(request.query_params['date'], '%Y-%m-%d').date()
        subject = self.get_object()
        qs = self.get_qs_date(subject, date)
        # serializer = getattr(settings.SERIALIZERS, f'class_{subject.id}_perfection')(qs, many=True)
        data = []
        class_ = self.get_class()
        for i in qs:
            serializer = getattr(settings.SERIALIZERS, f'class_{subject.id}_perfection')(i)
            _data = serializer.data
            _data['class_'] = PerfectionClassStudentInfoSerializer(
                i.perfection.classes.get(perfection_class=class_)
            ).data
            data.append(_data)
        return Response(data=data)

    @action(methods=['post'], detail=True)
    def check(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subject = self.get_object()
        data = serializer.validated_data
        _object = self.get_qs(subject).filter(id=data['id']).first()
        if _object is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"id": [f"{subject.name}不存在"]})
        if not _object.is_finished:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"non_field_errors": [f"该{subject.name}未完成，请等待学生完成后在评价"]}
            )
        if _object.is_checked:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"non_field_errors": [f"该{subject.name}已评价为{_object.rating}，不可修改"]}
            )
        _object.rating = data["rating"]
        _object.is_checked = True
        _object.checked = timezone.now()
        # 推送先不做，需要公共提醒模板
        _object.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True)
    def get_one(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        subject = self.get_object()
        data = serializer.validated_data
        _object = self.get_qs(subject).get(id=data['id'])
        _serializer = getattr(settings.SERIALIZERS, f'class_{subject.id}_perfection_detail')(
            _object, context=self.get_serializer_context()
        )
        data = _serializer.data
        data['class_'] = PerfectionClassStudentInfoSerializer(
            _object.perfection.classes.get(perfection_class=self.get_class())
        ).data
        return Response(data=data)


class PerfectionSubjectViewSet(viewsets.ModelViewSet):
    serializer_class = PerfectionSubjectSerializer
    queryset = PerfectionSubject.objects.all()
    permission_classes = settings.PERMISSIONS.class_subject
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return PerfectionSubjectCreateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.subject_create
        return super().get_permissions()


class WordsPagination(PageNumberPagination):
    # 默认的大小
    page_size = 10
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
        # if user.perfection.role == 'teacher':
        #     queryset = super().get_queryset()
        # else:
        queryset = user.perfection.words.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return WordsPerfectionListSerializer
        elif self.action == 'remember' or self.action == 'remember_file':
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
        # 向老师发送提醒
        for class_ in _object.perfection.classes.filter(perfection_class__subject__id="words"):
            date_str = _object.created.__format__('%Y-%m-%d')
            name = class_.nickname or _object.perfection.user.name
            data = {
                "title": f"{name}已提交打卡，请及时批改",
                "body": f"班级：{class_.perfection_class.name}({class_.perfection_class.id})学员[{name}]已提交"
                        f"{date_str}日单词打卡，请及时批改",
                "big_text": f"班级：{class_.perfection_class.name}({class_.perfection_class.id})学员[{name}]已提交"
                            f"{_object.created.__format__('%Y-%m-%d')}日单词打卡，请及时批改",
                "click_type": "intent",
                "payload": json.dumps(
                    {
                        "action": "open_page",
                        "url": f"/pages/perfection/teacher/class/subject/check"
                               f"?id={_object.id}"
                               f"&date={date_str}"
                               f"&class_id={class_.id}"
                               f"&sn={quote('单词打卡')}"
                               f"&subject=words"
                    }
                )
            }
            # print(data["payload"])
            to_single_alias(
                push=NotificationMessageOnline.objects.create(
                    **data,
                    channel_id="Push",
                    channel_name="Push",
                    channel_level=4
                ),
                channel=NotificationMessageOffline.objects.create(**data),
                group_name=date_str + '_teacher',
                alias=class_.perfection_class.teacher.user.uuid
            )
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
