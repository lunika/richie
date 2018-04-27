"""
Test suite for the wizard creating a new Organization page
"""
from django.core.urlresolvers import reverse

from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase

from apps.core.factories import UserFactory

from ..cms_wizards import OrganizationWizardForm
from ..factories import OrganizationFactory
from ..models import Organization


class OrganizationCMSWizardTestCase(CMSTestCase):
    """Organization tests"""

    def test_organization_create_wizards_list(self):
        """
        The wizard to create a new Organization page should be present on the wizards list page
        """
        user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=user.username, password='password')

        # Let the authorized user get the page with all wizards listed
        url = reverse('cms_wizard_create')
        response = self.client.get(url)

        # Check that our wizard to create organizations is on this page
        self.assertContains(
            response,
            '<span class="info">Create a new Organization page</span>',
            status_code=200,
            html=True,
        )
        self.assertContains(response, '<strong>New Organization page</strong>', html=True)

    def test_organization_wizard_submit_form(self):
        """
        Submitting a valid OrganizationWizardForm should create an organization and its
        related page.
        """
        # A parent page to list organizations should pre-exist
        create_page('Organizations', 'richie/fullwidth.html', 'en', reverse_id='organizations')

        # We can submit a form with just the title set
        form = OrganizationWizardForm(data={'title': 'My title'})
        self.assertTrue(form.is_valid())
        page = form.save()
        organization = page.organizationpage.organization

        # The organization and its related page should have been created as draft
        self.assertEqual(Page.objects.count(), 2)
        self.assertEqual(Page.objects.drafts().count(), 2)
        self.assertEqual(page.get_title(), 'My title')
        # The slug should have been automatically set
        self.assertEqual(page.get_slug(), 'my-title')
        # The code is left blank in this case
        self.assertIsNone(organization.code)

    def test_organization_wizard_submit_form_max_lengths(self):
        """
        Check that max lengths on each form field are compatible with max lengths on the
        Organization and Page models. Notably the "path" field on the Page model includes
        the slug + other elements for a max_length of 255.
        """
        # A parent page to list organizations should pre-exist
        create_page('Organizations', 'richie/fullwidth.html', 'en', reverse_id='organizations')

        # Submit values at max length on all fields
        data = {'title': 't' * 255, 'slug': 's' * 200}
        form = OrganizationWizardForm(data=data)

        self.assertTrue(form.is_valid())
        form.save()

        organizations = Organization.objects.all()
        self.assertEqual(len(organizations), 1)
        self.assertEqual(organizations[0].name, data['title'])
        self.assertIsNone(organizations[0].code)

    def test_organization_wizard_submit_form_slugify_long_title(self):
        """
        When generating the slug from the title, we should respect the slug's "max_length"
        """
        # A parent page to list organizations should pre-exist
        create_page('Organizations', 'richie/fullwidth.html', 'en', reverse_id='organizations')

        # Submit a title at max length
        data = {'title': 't' * 255}
        form = OrganizationWizardForm(data=data)
        self.assertTrue(form.is_valid())
        page = form.save()
        # Check that the slug has been truncated
        self.assertEqual(page.get_slug(), 't' * 200)

    def test_organization_wizard_submit_form_title_too_long(self):
        """
        Trying to set a title that is too long should make the form invalid
        """
        # Submit a title that is too long and a slug that is ok
        invalid_data = {'title': 't' * 256, 'slug': 's' * 200}

        form = OrganizationWizardForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        # Check that the title being too long is a cause for the invalid form
        self.assertEqual(
            form.errors['title'],
            ['Ensure this value has at most 255 characters (it has 256).'],
        )

    def test_organization_wizard_submit_form_slug_too_long(self):
        """
        Trying to set a slug that is too long should make the form invalid
        """
        # Submit a slug that is too long and a title that is ok
        invalid_data = {'title': 't' * 255, 'slug': 's' * 201}

        form = OrganizationWizardForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        # Check that the slug being too long is a cause for the invalid form
        self.assertEqual(
            form.errors['slug'],
            ['Ensure this value has at most 200 characters (it has 201).'],
        )

    def test_organization_wizard_parent_page_should_exist(self):
        """
        We should not be able to create a CMS Organization Page if the
        parent page to list organizations was not created
        """
        OrganizationFactory()
        form = OrganizationWizardForm(data={'title': 'My title'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'title': [
            'You must first create an `organization list` page and set its `reverse_id` to '
            '`organizations`.'
        ]})