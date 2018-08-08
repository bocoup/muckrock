"""
Custom pipeline steps for oAuth authentication
"""
# Standard Library
from datetime import date

# MuckRock
from muckrock.accounts.models import Profile


def associate_by_uuid(backend, details, user=None, *args, **kwargs):
    """Associate current auth with a user with the same uuid in the DB."""
    # pylint: disable=unused-argument
    if user:
        return None

    uuid = details.get('uuid')
    if uuid:
        try:
            profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            return None
        else:
            return {'user': profile.user, 'is_new': False}


def save_profile(backend, user, response, *args, **kwargs):
    """Save a profile for new users registered through squarelet"""
    # pylint: disable=unused-argument
    if not hasattr(user, 'profile'):
        user.profile = Profile(
            user=user,
            acct_type='basic',
            date_update=date.today(),
            uuid=response['uuid'],
        )

    old_email = user.email
    if 'email' in response:
        user.email = response['email']
        user.profile.email_confirmed = response['email_verified']
        if old_email != user.email:
            # if email has changed, update stripe customer and reset email failed flag
            customer = user.profile.customer()
            customer.email = user.email
            customer.save()
            user.profile.email_failed = False

    user.profile.full_name = response['name']
    if 'picture' in response:
        user.profile.avatar_url = response['picture']

    user.profile.save()
    user.save()
