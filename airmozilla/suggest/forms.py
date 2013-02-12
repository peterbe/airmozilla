from django import forms
from django.template.defaultfilters import slugify

from airmozilla.base.forms import BaseModelForm
from airmozilla.main.models import SuggestedEvent, Event, Tag, Participant


class StartForm(BaseModelForm):

    class Meta:
        model = SuggestedEvent
        fields = ('title', 'slug')

    def clean_slug(self):
        value = self.cleaned_data['slug']
        if value:
            if Event.objects.filter(slug__iexact=value):
                raise forms.ValidationError('Already taken')
        return value

    def clean(self):
        cleaned_data = super(StartForm, self).clean()
        if 'slug' in cleaned_data and 'title' in cleaned_data:
            if not cleaned_data['slug']:
                cleaned_data['slug'] = slugify(cleaned_data['title'])
                if Event.objects.filter(slug=cleaned_data['slug']):
                    raise forms.ValidationError('Slug already taken')
        return cleaned_data


class DescriptionForm(BaseModelForm):

    class Meta:
        model = SuggestedEvent
        fields = ('description', 'short_description')


class DetailsForm(BaseModelForm):

    tags = forms.CharField(required=False)

    class Meta:
        model = SuggestedEvent
        fields = (
            'location',
            'start_time',
            'privacy',
            'category',
            'tags',
            'channels',
            'additional_links',
        )

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        split_tags = [t.strip() for t in tags.split(',') if t.strip()]
        final_tags = []
        for tag_name in split_tags:
            t, __ = Tag.objects.get_or_create(name=tag_name)
            final_tags.append(t)
        return final_tags


class PlaceholderForm(BaseModelForm):

    class Meta:
        model = SuggestedEvent
        fields = ('placeholder_img',)


class ParticipantsForm(BaseModelForm):

    participants = forms.CharField(required=False)

    class Meta:
        model = SuggestedEvent
        fields = ('participants',)

    def clean_participants(self):
        participants = self.cleaned_data['participants']
        split_participants = [p.strip() for p in participants.split(',')
                              if p.strip()]
        final_participants = []
        for participant_name in split_participants:
            p = Participant.objects.get(name=participant_name)
            final_participants.append(p)
        return final_participants
