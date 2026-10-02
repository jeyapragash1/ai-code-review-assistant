"""Fail closed: personal installation ownership proves access without OAuth tokens.

Organization installation access requires an explicit administrator grant; login
allowlisting alone never grants access to another installation's private data.
"""
from sqlalchemy import or_, select, union
from app.models import GitHubInstallation, InstallationRepositoryAccess, UserInstallationAccess, UserRepositoryAccess


def owned_installation_ids(user):
    granted = select(UserInstallationAccess.installation_id).where(UserInstallationAccess.user_id == user.id,
        UserInstallationAccess.is_active.is_(True))
    return select(GitHubInstallation.id).where(or_(GitHubInstallation.account_github_id == user.github_user_id,
        GitHubInstallation.id.in_(granted)))


def owned_repository_ids(user, active=False):
    conditions = [InstallationRepositoryAccess.installation_id.in_(owned_installation_ids(user))]
    if active:
        conditions.extend([GitHubInstallation.is_active.is_(True), GitHubInstallation.suspended_at.is_(None),
            InstallationRepositoryAccess.is_active.is_(True)])
    installed = select(InstallationRepositoryAccess.repository_id).join(GitHubInstallation).where(*conditions)
    legacy = select(UserRepositoryAccess.repository_id).where(UserRepositoryAccess.user_id == user.id,
        UserRepositoryAccess.is_active.is_(True), ~select(InstallationRepositoryAccess.id).where(
            InstallationRepositoryAccess.repository_id == UserRepositoryAccess.repository_id).exists())
    return union(installed, legacy)


def accessible_repository_ids(user):
    return owned_repository_ids(user, active=True)
