from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import ForumTopic, ForumReply, db, User
from auth.forms import CreateTopicForm, ReplyForm
from utility import create_notification, send_topic_created_email, notify_forum_users

forum_bp = Blueprint('forum_bp', __name__)


@forum_bp.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    form = CreateTopicForm()
    if form.validate_on_submit():
        new_topic = ForumTopic(
            title=form.title.data,
            explanation=form.explanation.data,
            user_id=current_user.id
        )
        db.session.add(new_topic)
        db.session.commit()

        # Notify users who want forum notifications
        users = User.query.filter(User.notification_preferences.contains(['forum'])).all()
        for user in users:
            if current_user.id != user.id:
                create_notification(
                    user_id=user.id,
                    message=f"New discussion started: {new_topic.title} by {current_user.username}"
                )

                send_topic_created_email(
                user=user,
                f_topic_title=new_topic.title,
                f_topic_creator_name=current_user.username,             
                f_message=new_topic.explanation
                )

        flash('Topic created successfully!', 'success')
        return redirect(url_for('forum_bp.forum'))

    topics = ForumTopic.query.order_by(ForumTopic.created_at.desc()).all()
    return render_template('forum.html', form=form, topics=topics)


@forum_bp.route('/forum/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def topic_detail(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    form = ReplyForm()

    # Ownership check for the topic
    is_topic_owner = topic.user_id == current_user.id

    if form.validate_on_submit():
        new_reply = ForumReply(
            content=form.content.data,
            topic_id=topic_id,
            user_id=current_user.id
        )
        db.session.add(new_reply)
        db.session.commit()

        # Get the list of users who have replied to this topic (excluding duplicates)
        repliers = (
            User.query.join(ForumReply, User.id == ForumReply.user_id)
            .filter(ForumReply.topic_id == topic_id, User.id != current_user.id)
            .distinct()
            .all()
        )

        # Notify the topic owner and repliers
        notify_forum_users(
            topic_title=topic.title,
            topic_replier_name=current_user.username,
            topic_owner_id=topic.user_id,
            repliers=repliers,
            reply_message=form.content.data
        )

        flash('Reply posted successfully!', 'success')
        return redirect(url_for('forum_bp.topic_detail', topic_id=topic_id))

    # Fetch replies and include ownership information
    replies = [
        {
            'id': reply.id,
            'content': reply.content,
            'user': reply.user,  # Assuming `reply.user` provides the user object
            'created_at': reply.created_at,
            'is_owner': reply.user_id == current_user.id
        }
        for reply in ForumReply.query.filter_by(topic_id=topic_id).order_by(ForumReply.created_at).all()
    ]

    return render_template('topic_detail.html', topic=topic, replies=replies, form=form, is_topic_owner=is_topic_owner)


@forum_bp.route('/forum/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)

    # Ensure the current user owns the topic or has admin privileges
    if current_user.is_admin():
        pass
    elif topic.user_id != current_user.id:
        flash('You do not have permission to delete this topic.', 'danger')
        return redirect(url_for('forum_bp.topic_detail', topic_id=topic_id))

    try:
        db.session.delete(topic)  # This will also delete all related replies due to cascading
        db.session.commit()
        flash('Topic and its replies have been deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting topic: {str(e)}', 'danger')

    return redirect(url_for('forum_bp.forum'))


@forum_bp.route('/forum/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
def delete_reply(reply_id):
    reply = ForumReply.query.get_or_404(reply_id)

    # Ensure the current user owns the reply or has admin privileges
    if current_user.is_admin():
        pass
    elif reply.user_id != current_user.id:
        flash('You do not have permission to delete this reply.', 'danger')
        return redirect(url_for('forum_bp.topic_detail', topic_id=reply.topic_id))

    try:
        db.session.delete(reply)
        db.session.commit()
        flash('Reply has been deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting reply: {str(e)}', 'danger')

    return redirect(url_for('forum_bp.topic_detail', topic_id=reply.topic_id))
