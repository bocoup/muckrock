"""
Views for the project application
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count, Prefetch
from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator

from actstream.models import followers

from muckrock.crowdfund.models import Crowdfund
from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm
from muckrock.views import MRFilterableListView


class ProjectExploreView(TemplateView):
    """Provides a space for exploring our different projects."""
    template_name = 'project/frontpage.html'

    def get_context_data(self, **kwargs):
        """Gathers and returns a dictionary of context."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        user = self.request.user
        visible_projects = (Project.objects.get_visible(user)
                .order_by('-featured', 'title')
                .annotate(request_count=Count('requests', distinct=True))
                .annotate(article_count=Count('articles', distinct=True))
                .prefetch_related(
                    Prefetch('crowdfunds',
                        queryset=Crowdfund.objects
                            .order_by('-date_due')
                            .annotate(contributors_count=Count('payments'))))
                )
        context = {
            'visible': visible_projects,
        }
        return context


class ProjectListView(MRFilterableListView):
    """List all projects"""
    model = Project
    template_name = 'project/list.html'
    paginate_by = 25

    def get_queryset(self):
        """Only returns projects that are visible to the current user."""
        user = self.request.user
        if user.is_anonymous():
            return Project.objects.get_public()
        else:
            return Project.objects.get_visible(user)


class ProjectCreateView(CreateView):
    """Create a project instance"""
    model = Project
    form_class = ProjectCreateForm
    initial = {'private': True}
    template_name = 'project/create.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff or u.profile.experimental))
    def dispatch(self, *args, **kwargs):
        """At the moment, only staff are allowed to create a project."""
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Saves the current user as a contributor to the project."""
        redirection = super(ProjectCreateView, self).form_valid(form)
        project = self.object
        project.contributors.add(self.request.user)
        project.save()
        return redirection

class ProjectDetailView(DetailView):
    """View a project instance"""
    model = Project
    template_name = 'project/detail.html'

    def __init__(self, *args, **kwargs):
        self._obj = None
        super(ProjectDetailView, self).__init__(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        """Cache getting the object"""
        if self._obj is not None:
            return self._obj
        self._obj = super(ProjectDetailView, self).get_object(*args, **kwargs)
        return self._obj

    def get_context_data(self, **kwargs):
        """Adds visible requests and followers to project context"""
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = context['object']
        user = self.request.user
        context['sidebar_admin_url'] = reverse('admin:project_project_change',
            args=(project.pk,))
        context['visible_requests'] = (project.requests
                .get_viewable(user)
                .select_related(
                    'jurisdiction',
                    'jurisdiction__parent',
                    'jurisdiction__parent__parent',
                    ))
        context['followers'] = followers(project)
        context['articles'] = project.articles.get_published()
        context['contributors'] = project.contributors.select_related('profile')
        context['user_is_experimental'] = user.is_authenticated() and user.profile.experimental
        context['newsletter_label'] = ('Subscribe to the project newsletter'
                                      if not project.newsletter_label else project.newsletter_label)
        context['newsletter_cta'] = ('Get updates delivered to your inbox'
                                    if not project.newsletter_cta else project.newsletter_cta)
        context['user_can_edit'] = user.is_staff or user in project.contributors.all()
        return context

    def dispatch(self, *args, **kwargs):
        """If the project is private it is only visible to contributors and staff."""
        project = self.get_object()
        user = self.request.user
        contributor_or_staff = user.is_staff or project.has_contributor(user)
        if project.private and not contributor_or_staff:
            raise Http404()
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)


class ProjectPermissionsMixin(object):
    """
    This mixin provides a test to see if the current user is either
    a staff member or a project contributor. If they are, they are
    granted access to the page. If they aren't, a PermissionDenied
    exception is thrown.

    Note: It must be included first when subclassing Django generic views
    because it overrides their dispatch method.
    """

    def _is_editable_by(self, user):
        """A project is editable by MuckRock staff and project contributors."""
        project = self.get_object()
        return project.has_contributor(user) or user.is_staff

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Overrides the dispatch function to include permissions checking."""
        if not self._is_editable_by(self.request.user):
            raise Http404()
        return super(ProjectPermissionsMixin, self).dispatch(*args, **kwargs)


class ProjectEditView(ProjectPermissionsMixin, UpdateView):
    """Update a project instance"""
    model = Project
    template_name = 'project/edit.html'
    form_class = ProjectUpdateForm


class ProjectDeleteView(ProjectPermissionsMixin, DeleteView):
    """Delete a project instance"""
    model = Project
    success_url = reverse_lazy('index')
    template_name = 'project/delete.html'
