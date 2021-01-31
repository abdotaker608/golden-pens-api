from django.db import models
from django.db.models import Count, Q, Value
from django.db.models.functions import Concat, Greatest
from django.contrib.postgres.search import TrigramSimilarity
from urllib.parse import unquote
import datetime


class StoryManager(models.Manager):

    def find(self, search=None, cat=None, sub_cat=None, sub_cat_ar=None, sort='-created',
             follower_pk=None, author_id=None):

        queryset = self.model.objects.all()

        if author_id is not None:
            queryset = queryset.filter(author__pk=author_id)

        if follower_pk is not None:
            queryset = queryset.filter(author__followers__pk=follower_pk)

        if cat is not None:
            queryset = queryset.filter(category=cat)

        if search is not None or sub_cat is not None:

            query_conditions = Q(similarity__gte=0.1) | Q(name_similarity__gte=0.1)

            if search:
                query_conditions |= Q(category__trigram_similar=search)

            for i in range(30):
                if search is not None:
                    query_conditions |= Q(**{f'tags__{i}__trigram_similar': search})
                if sub_cat is not None:
                    query_conditions |= Q(**{f'tags__{i}__trigram_similar': sub_cat}) |\
                                        Q(**{f'tags__{i}__trigram_similar': unquote(u"%s" % sub_cat_ar)})

            queryset = queryset.annotate(fullname=Concat('author__user__first_name', Value(' '),
                                                         'author__user__last_name')) \
                .annotate(similarity=Greatest(
                        TrigramSimilarity('title', search),
                        TrigramSimilarity('title', sub_cat),
                ), name_similarity=Greatest(
                        TrigramSimilarity('fullname', search),
                        TrigramSimilarity('author__nickname', search)
                )).filter(query_conditions)

        if sort == 'relevance':
            if search is not None or sub_cat is not None:
                queryset = queryset.order_by('-similarity', '-name_similarity')
            else:
                queryset = queryset.order_by('-created')
        elif sort == 'mostViewed':
            queryset = queryset.annotate(trend=Count('chapters__views')).order_by('-trend', '-created')
        elif sort == 'trending':
            expired = datetime.date.today() - datetime.timedelta(days=7)
            queryset = queryset.filter(created__date__gte=expired).\
                annotate(trend=Count('chapters__views')).order_by('-trend', '-created')
        else:
            queryset = queryset.order_by(sort)

        return queryset

    def trending(self, limit=None):
        expired = datetime.date.today() - datetime.timedelta(days=7)
        if limit is not None:
            queryset = self.model.objects.filter(created__date__gte=expired).annotate(trend=Count('chapters__views'))\
                        .order_by('-trend', '-created')[:limit]
        else:
            queryset = self.model.objects.filter(created__date__gte=expired).annotate(trend=Count('chapters__views'))\
                        .order_by('-trend', '-created')
        return queryset

    def latest(self, limit=None):
        if limit is not None:
            queryset = self.model.objects.order_by('-created')[:limit]
        else:
            queryset = self.model.objects.order_by('-created')

        return queryset

    def personal(self, pk, sort='-created', limit=None):
        if limit is not None:
            queryset = self.model.objects.filter(author__pk=pk).order_by(sort)[:limit]
        else:
            queryset = self.model.objects.filter(author__pk=pk).order_by(sort)
        return queryset

    def following(self, pk, sort='-created', limit=None):
        if limit is not None:
            queryset = self.model.objects.filter(author__followers__pk=pk).order_by(sort)[:limit]
        else:
            queryset = self.model.objects.filter(author__followers__pk=pk).order_by(sort)
        return queryset
