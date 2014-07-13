# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

from captcha.fields import ReCaptchaField
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from django.forms import EmailField, Form, CharField, widgets, PasswordInput
from django.utils.translation import ugettext as _
from wger.core.models import UserProfile


class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('show_comments',
                  'show_english_ingredients',
                  'workout_reminder_active',
                  'workout_reminder',
                  'workout_duration',
                  'notification_language',
                  'timer_active',
                  'timer_pause')


class UserEmailForm(forms.ModelForm):
    email = EmailField(label=_("Email"),
                       help_text=_("Only needed to reset your password in case you forget it."),
                       required=False)

    class Meta:
        model = User
        fields = ('email', )

    def clean_email(self):
        '''
        Email must be unique system wide

        However, this check should only be performed when the user changes his
        email, otherwise the uniqueness check will because it will find one user
        (the current one) using the same email. Only when the user changes it, do
        we want to check that nobody else has that email
        '''

        email = self.cleaned_data["email"]
        if not email:
            return email
        try:
            user = User.objects.get(email=email)
            if user.email == self.instance.email:
                return email
        except User.DoesNotExist:
            return email

        raise ValidationError(_("This email is already used."))


class UserPersonalInformationForm(UserEmailForm):
    first_name = forms.CharField(label=_('First name'),
                                 required=False)
    last_name = forms.CharField(label=_('Last name'),
                                required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class GymUserAddForm(UserPersonalInformationForm):
    '''
    Form used when adding a user to a gym
    '''
    USER = 'user'
    GYM_ADMIN = 'admin'
    TRAINER = 'trainer'
    ROLES = (
        (USER, _('User')),
        (TRAINER, _('Trainer')),
        (GYM_ADMIN, _('Gym administrator')),
    )

    role = forms.ChoiceField(choices=ROLES,
                             initial=USER)
    username = forms.RegexField(label=_("Username"),
                                max_length=30,
                                regex=r'^[\w.@-]$',
                                help_text=_("Required. 30 characters or fewer. Letters, digits and "
                                            "@/.//-/_ only."),
                                error_messages={
                                'invalid': _("This value may contain only letters, numbers and "
                                             "@/.//-/_ characters.")})

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'role',)

    def clean_username(self):
        '''
        Since User.username is unique, this check is redundant,
        but it sets a nicer error message than the ORM. See #13147.
        '''
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))


class PasswordConfirmationForm(Form):
    '''
    A simple password confirmation form.

    This can be used to make sure the user really wants to perform a dangerous
    action. The form must be initialised with a user object.
    '''
    password = CharField(label=_("Password"),
                         widget=PasswordInput,
                         help_text=_('Please enter your current password.'))

    def __init__(self, user, data=None):
        self.user = user
        super(PasswordConfirmationForm, self).__init__(data=data)

    def clean_password(self):
        '''
        Check that the password supplied matches the one for the user
        '''
        password = self.cleaned_data.get('password', None)
        if not self.user.check_password(password):
            raise ValidationError(_('Invalid password'))
        return self.cleaned_data.get("password")


class RegistrationForm(UserCreationForm, UserEmailForm):
    '''
    Registration form
    '''
    captcha = ReCaptchaField(attrs={'theme': 'clean'},
                             label=_('Confirmation text'),
                             help_text=_('As a security measure, please enter the previous words'),)


class RegistrationFormNoCaptcha(UserCreationForm, UserEmailForm):
    '''
    Registration form without captcha field

    This is used when registering through an app, in that case there is not
    such a spam danger and simplifies the registration process on a mobile
    device.
    '''
    pass


class FeedbackRegisteredForm(forms.Form):
    '''
    Feedback form used for logged in users
    '''
    comment = forms.CharField(max_length=500,
                              min_length=10,
                              widget=widgets.Textarea,
                              help_text=_('What do you want to say?'),
                              required=True)


class FeedbackAnonymousForm(FeedbackRegisteredForm):
    '''
    Feedback form used for anonymous users (has additionally a reCaptcha field)
    '''
    captcha = ReCaptchaField(attrs={'theme': 'clean'},
                             label=_('Confirmation text'),
                             help_text=_('As a security measure, please enter the previous words'),)
