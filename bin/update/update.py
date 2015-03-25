"""
Deploy this project in dev/stage/production.

Requires commander_ which is installed on the systems that need it.

.. _commander: https://github.com/oremj/commander
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups
import commander_settings as settings

venv_path = '../venv'


@task
def update_code(ctx, tag):
    """Update the code to a specific git reference (tag/sha/etc)."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('git checkout %s' % tag)
        ctx.local('git pull -f')
        ctx.local("find . -type f -name '*.pyc' -delete")
        # Creating a virtualenv tries to open virtualenv/bin/python for
        # writing, but because virtualenv is using it, it fails.
        # So we delete it and let virtualenv create a new one.
        ctx.local('rm -f %s/bin/python' % venv_path)
        ctx.local('virtualenv %s' % venv_path)

        # Activate virtualenv to append to path.
        activate_env = os.path.join(
            settings.SRC_DIR, venv_path, 'bin', 'activate_this.py'
        )
        execfile(activate_env, dict(__file__=activate_env))

        ctx.local('%s/bin/pip install bin/peep-2.1.1.tar.gz' % venv_path)
        ctx.local('%s/bin/peep install -r requirements.txt' % venv_path)
        ctx.local('virtualenv --relocatable %s' % venv_path)


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local(
            '%s/bin/python manage.py collectstatic --noinput' % venv_path
        )


@task
def update_db(ctx):
    """Update the database schema, if necessary."""

    with ctx.lcd(settings.SRC_DIR):
        ctx.local(
            '%s/bin/python manage.py syncdb' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate --delete-ghost-migrations '
            '--noinput airmozilla.main' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.comments' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.uploads' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.subtitles' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.search' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.surveys' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.cronlogger' % venv_path
        )
        ctx.local(
            '%s/bin/python manage.py migrate airmozilla.starred' % venv_path
        )


@task
def install_cron(ctx):
    """Use gen-crons.py method to install new crontab."""

    with ctx.lcd(settings.SRC_DIR):
        ctx.local(
            '%s/bin/python ./bin/crontab/gen-crons.py -p '
            '%s/bin/python -w %s -u apache > /etc/cron.d/%s_generated' % (
                venv_path,
                venv_path,
                settings.SRC_DIR,
                settings.REMOTE_HOSTNAME,
            )
        )


@task
def checkin_changes(ctx):
    """Use the local, IT-written deploy script to check in changes."""
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(
    settings.WEB_HOSTGROUP,
    remote_kwargs={'ssh_key': settings.SSH_KEY}
)
def deploy_app(ctx):
    """Call the remote update script to push changes to webheads."""
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/etc/init.d/httpd graceful')


@hostgroups(
    settings.CELERY_HOSTGROUP,
    remote_kwargs={'ssh_key': settings.SSH_KEY}
)
def update_celery(ctx):
    """Update and restart Celery."""
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/sbin/service %s restart' % settings.CELERY_SERVICE)


@task
def update_info(ctx):
    """Write info about the current state to a publicly visible file."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date')
        ctx.local('git branch')
        ctx.local('git log -3')
        ctx.local('git status')
        ctx.local('git submodule status')

        ctx.local('git rev-parse HEAD > media/revision')


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    """Update code to pick up changes to this file."""
    update_code(ref)


@task
def update(ctx):
    update_assets()
    update_db()


@task
def deploy(ctx):
    install_cron()
    checkin_changes()
    deploy_app()
    # update_celery()
    update_info()


@task
def update_site(ctx, tag):
    """Update the app to prep for deployment."""
    pre_update(tag)
    update()
