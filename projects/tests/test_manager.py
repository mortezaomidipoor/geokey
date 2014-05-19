from django.test import TestCase
from django.core.exceptions import PermissionDenied

from nose.tools import raises

from dataviews.tests.model_factories import ViewFactory, ViewGroupFactory

from .model_factories import UserF, ProjectF
from ..models import Project


class ProjectListTest(TestCase):
    def setUp(self):
        self.creator = UserF.create()
        self.admin = UserF.create()
        self.contributor = UserF.create()
        self.non_member = UserF.create()
        self.view_member = UserF.create()

        self.public_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            add_viewers=[self.view_member],
            **{
                'isprivate': False
            }
        )

        self.private_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            add_viewers=[self.view_member]
        )

        self.inactive_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            add_viewers=[self.view_member],
            **{
                'status': 'inactive'
            }
        )

        self.deleted_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            add_viewers=[self.view_member],
            **{'isprivate': False}
        )
        self.deleted_project.delete()

    def test_get_projects_with_admin(self):
        projects = Project.objects.get_list(self.admin)
        self.assertEqual(projects.count(), 3)
        self.assertNotIn(self.deleted_project, projects)

    def test_get_projects_with_contributor(self):
        projects = Project.objects.get_list(self.contributor)
        self.assertEqual(projects.count(), 2)
        self.assertNotIn(self.inactive_project, projects)
        self.assertNotIn(self.deleted_project, projects)

    def test_get_projects_with_view_member(self):
        projects = Project.objects.get_list(self.view_member)
        self.assertEqual(projects.count(), 2)
        self.assertNotIn(self.inactive_project, projects)
        self.assertNotIn(self.deleted_project, projects)

    def test_get_projects_with_non_member(self):
        projects = Project.objects.get_list(self.non_member)
        self.assertEqual(projects.count(), 1)
        self.assertNotIn(self.private_project, projects)
        self.assertNotIn(self.inactive_project, projects)
        self.assertNotIn(self.deleted_project, projects)


class DeletedProjectTest(TestCase):
    def setUp(self):
        self.creator = UserF.create()
        self.admin = UserF.create()
        self.contributor = UserF.create()
        self.non_member = UserF.create()

        self.deleted_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor]
        )
        self.deleted_project.delete()

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_contributor_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.deleted_project
            })
        })

        Project.objects.as_contributor(
            self.view_member, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_contributor_with_non_member(self):
        Project.objects.as_contributor(
            self.non_member, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_contributor_with_contributor(self):
        Project.objects.as_contributor(
            self.contributor, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_contributor_with_admin(self):
        Project.objects.as_contributor(self.admin, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_admin_with_non_member(self):
        Project.objects.as_admin(self.non_member, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_admin_with_contributor(self):
        Project.objects.as_admin(self.contributor, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_as_admin_with_admin(self):
        Project.objects.as_admin(self.admin, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_with_non_member(self):
        Project.objects.get_single(self.non_member, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.deleted_project
            })
        })
        Project.objects.get_single(self.view_member, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_with_admin(self):
        Project.objects.get_single(self.admin, self.deleted_project.id)

    @raises(Project.DoesNotExist)
    def test_get_deleted_project_with_contributor(self):
        Project.objects.get_single(self.contributor, self.deleted_project.id)


class PrivateProjectTest(TestCase):
    def setUp(self):
        self.creator = UserF.create()
        self.admin = UserF.create()
        self.contributor = UserF.create()
        self.non_member = UserF.create()

        self.private_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor]
        )

    def test_get_private_project_with_admin(self):
        project = Project.objects.get_single(
            self.admin, self.private_project.id)
        self.assertEqual(project, self.private_project)

    def test_get_private_project_with_contributor(self):
        project = Project.objects.get_single(
            self.contributor,
            self.private_project.id
        )
        self.assertEqual(project, self.private_project)

    def test_get_private_project_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.private_project
            })
        })

        project = Project.objects.get_single(
            self.view_member,
            self.private_project.id
        )
        self.assertEqual(project, self.private_project)

    @raises(PermissionDenied)
    def test_get_private_project_with_non_member(self):
        Project.objects.get_single(self.non_member, self.private_project.id)

    def test_get_private_project_as_admin_with_admin(self):
        project = Project.objects.as_admin(self.admin, self.private_project.id)
        self.assertEqual(project, self.private_project)

    @raises(PermissionDenied)
    def test_get_private_project_as_admin_with_contributor(self):
        Project.objects.as_admin(self.contributor, self.private_project.id)

    @raises(PermissionDenied)
    def test_get_private_project_as_admin_with_non_member(self):
        Project.objects.as_admin(self.non_member, self.private_project.id)

    def test_get_private_project_as_contributor_with_admin(self):
        project = Project.objects.as_contributor(
            self.admin, self.private_project.id)
        self.assertEqual(project, self.private_project)

    def test_get_private_project_as_contributor_with_contributor(self):
        project = Project.objects.as_contributor(
            self.contributor, self.private_project.id)
        self.assertEqual(project, self.private_project)

    @raises(PermissionDenied)
    def test_get_private_project_as_contributor_with_non_member(self):
        Project.objects.as_contributor(
            self.non_member, self.private_project.id)

    @raises(PermissionDenied)
    def test_get_private_project_as_contributor_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.private_project
            })
        })

        Project.objects.as_contributor(
            self.view_member, self.private_project.id)


class InactiveProjectTest(TestCase):
    def setUp(self):
        self.creator = UserF.create()
        self.admin = UserF.create()
        self.contributor = UserF.create()
        self.non_member = UserF.create()

        self.inactive_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            **{
                'status': 'inactive'
            }
        )

    @raises(PermissionDenied)
    def test_get_inactive_project_with_admin(self):
        Project.objects.get_single(
            self.admin, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_with_contributor(self):
        Project.objects.get_single(self.contributor, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.inactive_project
            })
        })

        Project.objects.get_single(self.view_member, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_with_non_member(self):
        Project.objects.get_single(self.non_member, self.inactive_project.id)

    def test_get_inactive_project_as_admin_with_admin(self):
        project = Project.objects.as_admin(
            self.admin,
            self.inactive_project.id
        )
        self.assertEqual(project, self.inactive_project)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_admin_with_contributor(self):
        Project.objects.as_admin(self.contributor, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_admin_with_non_member(self):
        Project.objects.as_admin(self.non_member, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_contributor_with_admin(self):
        project = Project.objects.as_contributor(
            self.admin,
            self.inactive_project.id
        )
        self.assertEqual(project, self.inactive_project)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_contributor_with_contributor(self):
        Project.objects.as_contributor(
            self.contributor, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_contributor_with_non_member(self):
        Project.objects.as_contributor(
            self.non_member, self.inactive_project.id)

    @raises(PermissionDenied)
    def test_get_inactive_project_as_contributor_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.inactive_project
            })
        })

        Project.objects.as_contributor(
            self.view_member, self.inactive_project.id)


class PublicProjectTest(TestCase):
    def setUp(self):
        self.creator = UserF.create()
        self.admin = UserF.create()
        self.contributor = UserF.create()
        self.non_member = UserF.create()

        self.public_project = ProjectF.create(
            add_admins=[self.admin, self.creator],
            add_contributors=[self.contributor],
            **{
                'isprivate': False
            }
        )

    def test_get_public_project_with_admin(self):
        project = Project.objects.get_single(
            self.admin, self.public_project.id)
        self.assertEqual(project, self.public_project)

    def test_get_public_project_with_contributor(self):
        project = Project.objects.get_single(
            self.contributor, self.public_project.id)
        self.assertEqual(project, self.public_project)

    def test_get_public_project_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.public_project
            })
        })

        project = Project.objects.get_single(
            self.view_member, self.public_project.id)
        self.assertEqual(project, self.public_project)

    def test_get_public_project_with_non_member(self):
        project = Project.objects.get_single(
            self.non_member, self.public_project.id)
        self.assertEqual(project, self.public_project)

    def test_get_public_project_as_admin_with_admin(self):
        project = Project.objects.as_admin(self.admin, self.public_project.id)
        self.assertEqual(project, self.public_project)

    @raises(PermissionDenied)
    def test_get_public_project_as_admin_with_contributor(self):
        Project.objects.as_admin(self.contributor, self.public_project.id)

    @raises(PermissionDenied)
    def test_get_public_project_as_admin_with_non_member(self):
        Project.objects.as_admin(self.non_member, self.public_project.id)

    def test_get_public_project_as_contributor_with_admin(self):
        project = Project.objects.as_contributor(
            self.admin, self.public_project.id)
        self.assertEqual(project, self.public_project)

    def test_get_public_project_as_contributor_with_contributor(self):
        project = Project.objects.as_contributor(
            self.contributor, self.public_project.id)
        self.assertEqual(project, self.public_project)

    @raises(PermissionDenied)
    def test_get_public_project_as_contributor_with_non_member(self):
        Project.objects.as_contributor(self.non_member, self.public_project.id)

    @raises(PermissionDenied)
    def test_get_public_project_as_contributor_with_view_member(self):
        self.view_member = UserF.create()
        ViewGroupFactory(add_users=[self.view_member], **{
            'view': ViewFactory(**{
                'project': self.public_project
            })
        })

        Project.objects.as_contributor(
            self.view_member, self.public_project.id)
