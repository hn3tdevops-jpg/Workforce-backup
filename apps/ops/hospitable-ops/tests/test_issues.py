from apps.api.app.services.rbac_service import init_db
from apps.api.app.services.housekeeping import create_unit
from apps.api.app.services.issue import create_issue, transition_issue
from apps.api.app.models.housekeeping_models import IssueStatus


def setup_module(module):
    init_db()


def test_create_issue():
    u = create_unit('loc-issues', 'R201')
    issue, err = create_issue('loc-issues', u.id, category='plumbing', severity='high',
                               description='Leak under sink', created_by='user-1')
    assert err is None
    assert issue is not None
    assert issue.status == IssueStatus.OPEN
    assert issue.severity == 'high'


def test_issue_lifecycle():
    u = create_unit('loc-issues', 'R202')
    issue, _ = create_issue('loc-issues', u.id, category='electrical', severity='low',
                              description='Light flickers')
    issue, err = transition_issue(issue.id, IssueStatus.ACKNOWLEDGED)
    assert err is None
    assert issue.status == IssueStatus.ACKNOWLEDGED

    issue, err = transition_issue(issue.id, IssueStatus.IN_PROGRESS)
    assert err is None
    assert issue.status == IssueStatus.IN_PROGRESS

    issue, err = transition_issue(issue.id, IssueStatus.RESOLVED)
    assert err is None
    assert issue.status == IssueStatus.RESOLVED

    issue, err = transition_issue(issue.id, IssueStatus.CLOSED)
    assert err is None
    assert issue.status == IssueStatus.CLOSED


def test_issue_invalid_transition():
    u = create_unit('loc-issues', 'R203')
    issue, _ = create_issue('loc-issues', u.id, severity='med')
    # OPEN → RESOLVED is not allowed
    result, err = transition_issue(issue.id, IssueStatus.RESOLVED)
    assert result is None
    assert err == 'invalid_transition'


def test_issue_not_found():
    result, err = transition_issue('nonexistent-issue', IssueStatus.ACKNOWLEDGED)
    assert result is None
    assert err == 'issue_not_found'
