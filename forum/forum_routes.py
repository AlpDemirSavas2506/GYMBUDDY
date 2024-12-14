from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import ForumTopic, ForumReply, db, User
from auth.forms import CreateTopicForm, ReplyForm
from utility import create_notification, send_topic_created_email

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
    if form.validate_on_submit():
        new_reply = ForumReply(
            content=form.content.data,
            topic_id=topic_id,
            user_id=current_user.id
        )
        db.session.add(new_reply)
        db.session.commit()

        flash('Reply posted successfully!', 'success')
        return redirect(url_for('forum_bp.topic_detail', topic_id=topic_id))

    replies = ForumReply.query.filter_by(topic_id=topic_id).order_by(ForumReply.created_at).all()
    return render_template('topic_detail.html', topic=topic, replies=replies, form=form)


@forum_bp.route('/forum/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)

    # Ensure the current user owns the topic or has admin privileges
    if topic.user_id != current_user.id:
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
    if reply.user_id != current_user.id:
        flash('You do not have permission to delete this reply.', 'danger')
        return redirect(url_for('forum_bp.topic_detail', topic_id=reply.topic_id))

    try:
        db.session.delete(reply)
        db.session.commit()
        flash('Reply has been deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting reply: {str(e)}', 'danger')

    return redirect(url_for('forum_bp.topic_detail', topic_id=reply.topic_id))
