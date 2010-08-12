"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
import nose.tools

from datetime import date, timedelta
from operator import attrgetter

from foia.models import FOIARequest, FOIAImage, Jurisdiction, AgencyType
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

# allow methods that could be functions and too many public methods in tests
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

class TestFOIARequestUnit(TestCase):
    """Unit tests for FOIARequests"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_foiarequests.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable-msg=C0103
        self.foia = FOIARequest.objects.get(pk=1)

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        nose.tools.eq_(unicode(self.foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(self.foia.get_absolute_url(),
            reverse('foia-detail', kwargs={'idx': self.foia.id, 'slug': 'test-1',
                                           'jurisdiction': 'massachusetts'}))

    def test_foia_model_editable(self):
        """Test FOIA Request model's is_editable method"""

        foias = FOIARequest.objects.all().order_by('id')[:5]
        for foia in foias[:5]:
            if foia.status in ['started', 'fix']:
                nose.tools.assert_true(foia.is_editable())
            else:
                nose.tools.assert_false(foia.is_editable())

    def test_foia_email(self):
        """Test FOIA sending an email to the user when a FOIA request is updated"""

        nose.tools.eq_(len(mail.outbox), 0)

        self.foia.status = 'submitted'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 0)

        self.foia.status = 'processed'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[0].to, [self.foia.user.email])

        self.foia.status = 'fix'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 2)

        self.foia.status = 'rejected'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 3)

        self.foia.status = 'done'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 4)

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)

        foias = list(FOIARequest.objects.filter(id__in=[1, 5, 11, 12, 13, 14]).order_by('id'))
        foias[1].date_done = date.today() - timedelta(10)
        foias[2].date_done = date.today() - timedelta(10)
        foias[3].date_done = date.today() - timedelta(30)
        foias[4].date_done = date.today() - timedelta(90)

        # check manager get_viewable against models is_viewable
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user1))
            else:
                nose.tools.assert_false(foia.is_viewable(user1))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user2))
            else:
                nose.tools.assert_false(foia.is_viewable(user2))

        viewable_foias = FOIARequest.objects.get_viewable(AnonymousUser())
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(AnonymousUser()))
            else:
                nose.tools.assert_false(foia.is_viewable(AnonymousUser()))

        nose.tools.assert_true(foias[0].is_viewable(user1))
        nose.tools.assert_true(foias[1].is_viewable(user1))
        nose.tools.assert_true(foias[2].is_viewable(user1))
        nose.tools.assert_true(foias[3].is_viewable(user1))
        nose.tools.assert_true(foias[4].is_viewable(user1))

        nose.tools.assert_false(foias[0].is_viewable(user2))
        nose.tools.assert_true (foias[1].is_viewable(user2))
        nose.tools.assert_false(foias[2].is_viewable(user2))
        nose.tools.assert_true (foias[3].is_viewable(user2))
        nose.tools.assert_true (foias[4].is_viewable(user2))

        nose.tools.assert_false(foias[0].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[1].is_viewable(AnonymousUser()))
        nose.tools.assert_false(foias[2].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[3].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[4].is_viewable(AnonymousUser()))

     # manager
    def test_manager_get_submitted(self):
        """Test the FOIA Manager's get_submitted method"""

        submitted_foias = FOIARequest.objects.get_submitted()
        for foia in FOIARequest.objects.all():
            if foia in submitted_foias:
                nose.tools.ok_(foia.status in ['submitted', 'processed', 'fix', 'rejected', 'done'])
            else:
                nose.tools.ok_(foia.status == 'started')

    def test_manager_get_done(self):
        """Test the FOIA Manager's get_done method"""

        done_foias = FOIARequest.objects.get_done()
        for foia in FOIARequest.objects.all():
            if foia in done_foias:
                nose.tools.ok_(foia.status == 'done')
            else:
                nose.tools.ok_(
                        foia.status in ['started', 'submitted', 'processed', 'fix', 'rejected'])


class TestFOIAImageUnit(TestCase):
    """Unit tests for FOIARequests"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_foiarequests.json', 'test_foiaimages.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable-msg=C0103
        self.foia = FOIARequest.objects.get(pk=1)
        self.doc = FOIAImage.objects.get(pk=1)

    # models
    def test_foia_doc_model_unicode(self):
        """Test FOIA Image model's __unicode__ method"""
        nose.tools.eq_(unicode(self.doc), 'Test 5 Document Page 1')

    def test_foia_doc_model_url(self):
        """Test FOIA Images model's get_absolute_url method"""
        nose.tools.eq_(self.doc.get_absolute_url(),
            reverse('foia-doc-detail', kwargs={'idx': self.doc.foia.id, 'slug': self.doc.foia.slug,
                                               'jurisdiction': self.doc.foia.jurisdiction.slug,
                                               'page': self.doc.page}))

    def test_foia_doc_next_prev(self):
        """Test FOIA Images model's next and previous methods"""

        foia = FOIARequest.objects.get(pk=10)
        doc1 = FOIAImage.objects.get(foia=foia, page=1)
        doc2 = FOIAImage.objects.get(foia=foia, page=2)
        doc3 = FOIAImage.objects.get(foia=foia, page=3)
        nose.tools.eq_(doc1.previous(), None)
        nose.tools.eq_(doc1.next(), doc2)
        nose.tools.eq_(doc2.previous(), doc1)
        nose.tools.eq_(doc2.next(), doc3)
        nose.tools.eq_(doc3.previous(), doc2)
        nose.tools.eq_(doc3.next(), None)

    def test_foia_doc_total_pages(self):
        """Test FOIA Images model's total pages method"""
        foia = FOIARequest.objects.get(pk=10)
        doc1 = FOIAImage.objects.get(foia=foia, page=1)
        doc2 = FOIAImage.objects.get(foia=foia, page=2)
        doc3 = FOIAImage.objects.get(foia=foia, page=3)

        nose.tools.eq_(self.doc.total_pages(), 1)
        nose.tools.eq_(doc1.total_pages(), 3)
        nose.tools.eq_(doc2.total_pages(), 3)
        nose.tools.eq_(doc3.total_pages(), 3)


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json', 'test_profiles.json',
                'test_foiarequests.json', 'test_foiaimages.json']

    # views
    def test_foia_list(self):
        """Test the foia-list view"""

        response = get_allowed(self.client, reverse('foia-list'),
                ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(set(response.context['object_list']),
                set(FOIARequest.objects.get_viewable(AnonymousUser())[:10]))

    def test_foia_list_user(self):
        """Test the foia-list-user view"""

        for username in ['adam', 'bob']:
            response = get_allowed(self.client,
                                   reverse('foia-list-user', kwargs={'user_name': username}),
                                   ['foia/foiarequest_list.html', 'foia/base.html'])
            user = User.objects.get(username=username)
            nose.tools.eq_(set(response.context['object_list']),
                           set(FOIARequest.objects.get_viewable(AnonymousUser()).filter(user=user)))
            nose.tools.ok_(all(foia.user == user for foia in response.context['object_list']))

    def test_foia_sorted_list(self):
        """Test the foia-sorted-list view"""

        for field, attr in [('title', 'title'), ('user', 'user.username'),
                            ('status', 'status'), ('jurisdiction', 'jurisdiction.name')]:
            for order in ['asc', 'desc']:

                response = get_allowed(self.client, reverse('foia-sorted-list',
                                       kwargs={'sort_order': order, 'field': field}),
                                       ['foia/foiarequest_list.html', 'foia/base.html'])
                nose.tools.eq_([f.title for f in response.context['object_list']],
                               [f.title for f in sorted(response.context['object_list'],
                                                        key=attrgetter(attr),
                                                        reverse=order=='desc')])

    def test_foia_detail(self):
        """Test the foia-detail view"""

        foia = FOIARequest.objects.get(pk=2)
        get_allowed(self.client,
                    reverse('foia-detail', kwargs={'idx': foia.pk, 'slug': foia.slug,
                                                   'jurisdiction': foia.jurisdiction.slug}),
                    ['foia/foiarequest_detail.html', 'foia/base.html'],
                    context = {'object': foia})

    def test_foia_doc_detail(self):
        """Test the foia-doc-detail view"""

        # Need a way to put an actual image in here for this to work
        #get_allowed(self.client,
        #            reverse('foia-doc-detail',
        #                kwargs={'user_name': 'test1', 'slug': 'test-a', 'page': 1,
        #                        'jurisdiction': 'massachusetts'}),
        #            ['foia/foiarequest_doc_detail.html', 'foia/base.html'],
        #            context = {'doc': doc1})

    def test_feeds(self):
        """Test the RSS feed views"""

        get_allowed(self.client, reverse('foia-submitted-feed'))
        get_allowed(self.client, reverse('foia-done-feed'))

    def test_404_views(self):
        """Test views that should give a 404 error"""

        get_404(self.client, reverse('foia-list-user', kwargs={'user_name': 'test3'}))
        get_404(self.client, reverse('foia-sorted-list',
                kwargs={'sort_order': 'asc', 'field': 'bad_field'}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 1, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 2, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 3, 'slug': 'test-c', 'page': 3,
                                        'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 4, 'slug': 'test-c', 'page': 1,
                                        'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 5, 'slug': 'test-c', 'page': 1,
                                        'jurisdiction': 'massachusetts'}))

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        foia = FOIARequest.objects.get(pk=2)
        get_post_unallowed(self.client, reverse('foia-create'))
        get_post_unallowed(self.client, reverse('foia-update',
                                           kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                   'idx': foia.pk, 'slug': foia.slug}))

    def test_auth_views(self):
        """Test private views while logged in"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        # get authenticated pages
        get_allowed(self.client, reverse('foia-create'),
                    ['foia/foiawizard_where.html', 'foia/base-submit.html'])

        get_allowed(self.client, reverse('foia-update',
                                    kwargs={'jurisdiction': foia.jurisdiction.slug,
                                            'idx': foia.pk, 'slug': foia.slug}),
                    ['foia/foiarequest_form.html', 'foia/base-submit.html'])

        get_404(self.client, reverse('foia-update',
                                kwargs={'jurisdiction': foia.jurisdiction.slug,
                                        'idx': foia.pk, 'slug': 'bad_slug'}))

        # post authenticated pages
        post_allowed_bad(self.client, reverse('foia-create'),
                         ['foia/foiawizard_where.html', 'foia/base-submit.html'])
        post_allowed_bad(self.client, reverse('foia-update',
                                         kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                 'idx': foia.pk, 'slug': foia.slug}),
                         ['foia/foiarequest_form.html', 'foia/base-submit.html'])

    def test_post_views(self):
        """Test posting data in views while logged in"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        # test for submitting a foia request for enough credits
        # tests for the wizard

        foia_data = {'title': 'test a', 'request': 'updated request', 'submit': 'Submit Request',
                     'jurisdiction': Jurisdiction.objects.get(slug='boston-ma').pk,
                     'agency_type': AgencyType.objects.get(name='Clerk').pk}
                     

        post_allowed(self.client, reverse('foia-update',
                                     kwargs={'jurisdiction': foia.jurisdiction.slug,
                                             'idx': foia.pk, 'slug': foia.slug}),
                     foia_data, 'http://testserver' +
                     reverse('foia-detail', kwargs={'jurisdiction': 'boston-ma',
                                                    'idx': foia.pk, 'slug': 'test-a'}))
        foia = FOIARequest.objects.get(title='test a')
        nose.tools.eq_(foia.request, 'updated request')
        nose.tools.eq_(foia.status, 'submitted')
