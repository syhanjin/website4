# ==============================================================================
#  Copyright (C) 2023 Sakuyark, Inc. All Rights Reserved                       =
#                                                                              =
#    @Time : 2023-2-5 13:32                                                    =
#    @Author : hanjin                                                          =
#    @Email : 2819469337@qq.com                                                =
#    @File : views.py                                                          =
#    @Program: website                                                         =
# ==============================================================================
import random

from django.conf import settings as django_settings
from django.http import FileResponse
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from images.models import Image
from perfection.models.base import PerfectionStudent
from perfection.serializers.base import (
    PerfectionStudentChIdiomLibrariesSetSerializer, PerfectionStudentCreateSerializer, PerfectionStudentSerializer,
    PerfectionStudentWordLibrariesSetSerializer,
)
from perfection.utils.build_chIdiom_pdf import to_pdf as to_chIdiom_pdf
from perfection.utils.build_chWord_pdf import to_pdf as to_chWord_pdf
from perfection.utils.build_word_pdf import to_pdf as to_word_pdf
from .conf import settings
from .models.chIdioms import ChIdiomLibrary, ChIdiomsPerfection
from .models.chWords import ChWordLibrary, ChWordsPerfection
from .models.words import WordLibrary, WordsPerfection
from .serializers.chIdioms import (
    ChIdiomLibrarySerializer, ChIdiomsPerfectionAdditionSerializer, ChIdiomsPerfectionAllChIdiomsSerializer,
    ChIdiomsPerfectionFinishSerializer,
    ChIdiomsPerfectionListSerializer,
    ChIdiomsPerfectionRememberSerializer,
    ChIdiomsPerfectionReviewSerializer, ChIdiomsPerfectionSerializer, ChIdiomsPerfectionUnrememberedSerializer,
)
from .serializers.chWords import (
    ChWordLibrarySerializer, ChWordsPerfectionAdditionSerializer, ChWordsPerfectionAllChWordsSerializer,
    ChWordsPerfectionFinishSerializer, ChWordsPerfectionListSerializer,
    ChWordsPerfectionRememberSerializer, ChWordsPerfectionReviewSerializer, ChWordsPerfectionSerializer,
    ChWordsPerfectionUnrememberedSerializer,
)
from .serializers.words import (
    WordLibrarySerializer, WordsPerfectionAdditionSerializer, WordsPerfectionAllWordsSerializer,
    WordsPerfectionFinishSerializer,
    WordsPerfectionListSerializer,
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


def to_pdf_resp(words, to_pdf, updated, mode, addition=None):
    mode2text = {'review': '打卡版', 'remember': '记忆版'}
    date = updated.__format__("%Y-%m-%d")
    pdf = to_pdf(words=words, date=date, mode=mode, addition=addition)
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
        elif self.action == 'set_chIdioms_library':
            return PerfectionStudentChIdiomLibrariesSetSerializer
        elif self.action == 'set_chWords_library':
            return PerfectionStudentChWordLibrariesSetSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.student_create
        elif self.action == 'set_words_library':
            self.permission_classes = settings.PERMISSIONS.words_library_set
        elif self.action == 'set_chIdioms_library':
            self.permission_classes = settings.PERMISSIONS.chIdioms_library_set
        elif self.action == 'set_chWords_library':
            self.permission_classes = settings.PERMISSIONS.chWords_library_set
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

    @action(methods=['post'], detail=False)
    def set_chIdioms_library(self, request, *args, **kwargs):
        _object = self.get_instance().perfection
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        libraries = ChIdiomLibrary.objects.filter(id__in=serializer.validated_data['chIdiom_libraries'])
        _object.chIdiom_libraries.set(libraries)
        _object.save()
        return Response(
            data={'chIdiom_libraries': list(_object.chIdiom_libraries.all().values_list('name', flat=True))}
        )

    @action(methods=['post'], detail=False)
    def set_chWords_library(self, request, *args, **kwargs):
        _object = self.get_instance().perfection
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        libraries = ChWordLibrary.objects.filter(id__in=serializer.validated_data['chWord_libraries'])
        _object.chWord_libraries.set(libraries)
        _object.save()
        return Response(
            data={'chWord_libraries': list(_object.chWord_libraries.all().values_list('name', flat=True))}
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
        elif self.action == 'addition':
            return WordsPerfectionAdditionSerializer
        elif self.action == 'unremembered':
            return WordsPerfectionUnrememberedSerializer
        elif self.action == 'all_words':
            return WordsPerfectionAllWordsSerializer
        elif self.action == 'finish':
            return WordsPerfectionFinishSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.words_create
        # elif self.action == 'libraries':
        #     self.permission_classes = settings.PERMISSIONS.word_libraries
        elif self.action in ['remember', 'review', 'remember_file', 'review_file', 'unremembered',
                             'addition', 'all_words']:
            self.permission_classes = settings.PERMISSIONS.words
        elif self.action == 'finish':
            self.permission_classes = settings.PERMISSIONS.words_finish
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(methods=['get', 'post'], detail=True)
    def remember(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def unremembered(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def review(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['review'] = [x['word'] for x in data['review']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def addition(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['addition'] = [x['word'] for x in data['addition']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def remember_file(self, request, *args, **kwargs):
        instance = self.get_object()
        return to_pdf_resp(instance.remember.all(), to_word_pdf, instance.updated, mode='remember')

    @action(methods=['get'], detail=True)
    def review_file(self, request, *args, **kwargs):
        instance = self.get_object()
        words = list(instance.review.all())
        addition = list(instance.addition.all())
        random.shuffle(words)
        random.shuffle(addition)
        return to_pdf_resp(words, to_word_pdf, instance.updated, addition=addition, mode='review')

    @action(methods=['get'], detail=True)
    def all_words(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        _object = self.get_object()
        if _object.status == settings.CHOICES.words_perfection_status.FINISHED:
            # 伪造drf验证返回值
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['打卡已完成']})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        errors = {}
        review = _object.review.all()
        addition = _object.addition.all()
        if review.count() != len(data["review"].keys()):
            errors['review'] = "「打卡版·正常」词量不匹配"
        if addition.count() != len(data["addition"].keys()):
            errors['addition'] = "「打卡版·附加」词量不匹配"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        # 查验传入字典的单词
        review_errors = [x for x in data['review'].keys() if x not in review.values_list('word__word', flat=True)]
        if len(review_errors) > 0:
            errors['review'] = f"{review_errors} 不是本次「打卡版·正常」的单词"
        # print(addition.values_list('word__word', flat=True))
        addition_errors = [x for x in data['addition'].keys() if x not in addition.values_list('word__word', flat=True)]
        if len(addition_errors) > 0:
            errors['addition'] = f"{addition_errors} 不是本次「打卡版·附加」的单词"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        _object.update_words(
            review=data['review'],
            addition=data['addition']
        )
        # _object.picture = data['picture']
        # 处理图片问题
        for pic in data['picture']:
            image = Image.objects.create(image=pic)
            _object.picture.add(image)
        #
        _object.status = settings.CHOICES.words_perfection_status.FINISHED
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


# 语文成语打卡

class ChIdiomsPagination(PageNumberPagination):
    # 默认的大小
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 30


class ChIdiomsPerfectionViewSet(viewsets.ModelViewSet):
    serializer_class = ChIdiomsPerfectionSerializer
    queryset = ChIdiomsPerfection.objects.all()
    permission_classes = settings.PERMISSIONS.chIdioms
    lookup_field = 'id'
    pagination_class = ChIdiomsPagination

    def get_queryset(self):
        user = self.request.user
        # if user.perfection.role == 'teacher':
        #     queryset = super().get_queryset()
        # else:
        queryset = user.perfection.chIdioms.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ChIdiomsPerfectionListSerializer
        elif self.action == 'remember' or self.action == 'remember_file':
            return ChIdiomsPerfectionRememberSerializer
        elif self.action == 'review' or self.action == 'review_file':
            return ChIdiomsPerfectionReviewSerializer
        elif self.action == 'addition':
            return ChIdiomsPerfectionAdditionSerializer
        elif self.action == 'unremembered':
            return ChIdiomsPerfectionUnrememberedSerializer
        elif self.action == 'all_chIdioms':
            return ChIdiomsPerfectionAllChIdiomsSerializer
        elif self.action == 'finish':
            return ChIdiomsPerfectionFinishSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.chIdioms_create
        elif self.action in ['remember', 'review', 'remember_file', 'review_file', 'unremembered',
                             'addition', 'all_chIdioms']:
            self.permission_classes = settings.PERMISSIONS.chIdioms
        elif self.action == 'finish':
            self.permission_classes = settings.PERMISSIONS.chIdioms_finish
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(methods=['get', 'post'], detail=True)
    def remember(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def unremembered(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def review(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['review'] = [x['key'] for x in data['review']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def addition(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['addition'] = [x['key'] for x in data['addition']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def remember_file(self, request, *args, **kwargs):
        instance = self.get_object()
        return to_pdf_resp(instance.remember.all(), to_chIdiom_pdf, instance.updated, mode='remember')

    @action(methods=['get'], detail=True)
    def review_file(self, request, *args, **kwargs):
        instance = self.get_object()
        chIdioms = list(instance.review.all())
        addition = list(instance.addition.all())
        random.shuffle(chIdioms)
        random.shuffle(addition)
        return to_pdf_resp(chIdioms, to_chIdiom_pdf, instance.updated, addition=addition, mode='review')

    @action(methods=['get'], detail=True)
    def all_chIdioms(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        _object = self.get_object()
        if _object.status == settings.CHOICES.chIdioms_perfection_status.FINISHED:
            # 伪造drf验证返回值
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['打卡已完成']})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        errors = {}
        review = _object.review.all()
        addition = _object.addition.all()
        if review.count() != len(data["review"].keys()):
            errors['review'] = "「打卡版·正常」词量不匹配"
        if addition.count() != len(data["addition"].keys()):
            errors['addition'] = "「打卡版·附加」词量不匹配"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        # 查验传入字典的单词
        review_errors = [x for x in data['review'].keys() if x not in review.values_list('chIdiom__key', flat=True)]
        if len(review_errors) > 0:
            errors['review'] = f"{review_errors} 不是本次「打卡版·正常」的单词"
        addition_errors = [x for x in data['addition'].keys() if
                           x not in addition.values_list('chIdiom__key', flat=True)]
        if len(addition_errors) > 0:
            errors['addition'] = f"{addition_errors} 不是本次「打卡版·附加」的单词"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        _object.update_chIdioms(
            review=data['review'],
            addition=data['addition']
        )
        # _object.picture = data['picture']
        # 处理图片问题
        for pic in data['picture']:
            image = Image.objects.create(image=pic)
            _object.picture.add(image)
        #
        _object.status = settings.CHOICES.chIdioms_perfection_status.FINISHED
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
                "unremembered_chIdioms": _object.unremembered_chIdioms.values_list('chIdiom__key', 'chIdiom__value')
            }
        )


class ChIdiomLibraryViewSet(viewsets.ModelViewSet):
    serializer_class = ChIdiomLibrarySerializer
    queryset = ChIdiomLibrary.objects.all()
    permission_classes = settings.PERMISSIONS.chIdiom_libraries
    lookup_field = 'id'


# 语文文言字词打卡

class ChWordsPagination(PageNumberPagination):
    # 默认的大小
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 30


class ChWordsPerfectionViewSet(viewsets.ModelViewSet):
    serializer_class = ChWordsPerfectionSerializer
    queryset = ChWordsPerfection.objects.all()
    permission_classes = settings.PERMISSIONS.chWords
    lookup_field = 'id'
    pagination_class = ChWordsPagination

    def get_queryset(self):
        user = self.request.user
        # if user.perfection.role == 'teacher':
        #     queryset = super().get_queryset()
        # else:
        queryset = user.perfection.chWords.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ChWordsPerfectionListSerializer
        elif self.action == 'remember' or self.action == 'remember_file':
            return ChWordsPerfectionRememberSerializer
        elif self.action == 'review' or self.action == 'review_file':
            return ChWordsPerfectionReviewSerializer
        elif self.action == 'addition':
            return ChWordsPerfectionAdditionSerializer
        elif self.action == 'unremembered':
            return ChWordsPerfectionUnrememberedSerializer
        elif self.action == 'all_chWords':
            return ChWordsPerfectionAllChWordsSerializer
        elif self.action == 'finish':
            return ChWordsPerfectionFinishSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = settings.PERMISSIONS.chWords_create
        elif self.action in ['remember', 'review', 'remember_file', 'review_file', 'unremembered',
                             'addition', 'all_chWords']:
            self.permission_classes = settings.PERMISSIONS.chWords
        elif self.action == 'finish':
            self.permission_classes = settings.PERMISSIONS.chWords_finish
        return super().get_permissions()

    def get_instance(self):
        return self.request.user

    @action(methods=['get', 'post'], detail=True)
    def remember(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def unremembered(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def review(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['review'] = [x['key'] for x in data['review']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def addition(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object())
        data = serializer.data
        if request.query_params.get('simple'):
            data['addition'] = [x['key'] for x in data['addition']]
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def remember_file(self, request, *args, **kwargs):
        instance = self.get_object()
        return to_pdf_resp(instance.remember.all(), to_chWord_pdf, instance.updated, mode='remember')

    @action(methods=['get'], detail=True)
    def review_file(self, request, *args, **kwargs):
        instance = self.get_object()
        chWords = list(instance.review.all())
        addition = list(instance.addition.all())
        random.shuffle(chWords)
        random.shuffle(addition)
        return to_pdf_resp(chWords, to_chWord_pdf, instance.updated, addition=addition, mode='review')

    @action(methods=['get'], detail=True)
    def all_chWords(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def finish(self, request, *args, **kwargs):
        _object = self.get_object()
        if _object.status == settings.CHOICES.chWords_perfection_status.FINISHED:
            # 伪造drf验证返回值
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'non_field_errors': ['打卡已完成']})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        errors = {}
        review = _object.review.all()
        addition = _object.addition.all()
        if review.count() != len(data["review"].keys()):
            errors['review'] = "「打卡版·正常」词量不匹配"
        if addition.count() != len(data["addition"].keys()):
            errors['addition'] = "「打卡版·附加」词量不匹配"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        # 查验传入字典的单词
        review_errors = [x for x in data['review'].keys() if x not in review.values_list('chWord__key', flat=True)]
        if len(review_errors) > 0:
            errors['review'] = f"{review_errors} 不是本次「打卡版·正常」的单词"
        addition_errors = [x for x in data['addition'].keys() if
                           x not in addition.values_list('chWord__key', flat=True)]
        if len(addition_errors) > 0:
            errors['addition'] = f"{addition_errors} 不是本次「打卡版·附加」的单词"
        if len(errors.keys()) > 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        _object.update_chWords(
            review=data['review'],
            addition=data['addition']
        )
        # _object.picture = data['picture']
        # 处理图片问题
        for pic in data['picture']:
            image = Image.objects.create(image=pic)
            _object.picture.add(image)
        #
        _object.status = settings.CHOICES.chWords_perfection_status.FINISHED
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
                "unremembered_chWords": _object.unremembered_chWords.values_list(
                    'chWord__key', 'chWord__sentence', 'chWord__value'
                )
            }
        )


class ChWordLibraryViewSet(viewsets.ModelViewSet):
    serializer_class = ChWordLibrarySerializer
    queryset = ChWordLibrary.objects.all()
    permission_classes = settings.PERMISSIONS.chWord_libraries
    lookup_field = 'id'
