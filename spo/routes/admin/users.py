"""Admin routes for user management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import User


def register_admin_users(app):
    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.role != 'admin':
            flash('Zugriff verweigert. Nur Admins können User verwalten.', 'error')
            return redirect(url_for('admin'))
        
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/<int:user_id>/update_role', methods=['POST'])
    @login_required
    def admin_update_user_role(user_id):
        if current_user.role != 'admin':
            flash('Zugriff verweigert.', 'error')
            return redirect(url_for('admin'))
        
        user = User.query.get_or_404(user_id)
        new_role = request.form.get('role')
        
        if new_role not in ['viewer', 'user', 'contributor', 'admin']:
            flash('Ungültige Rolle.', 'error')
            return redirect(url_for('admin_users'))
        
        # Prevent admin from demoting themselves
        if user.id == current_user.id and new_role != 'admin':
            flash('Sie können Ihre eigene Admin-Rolle nicht entfernen.', 'error')
            return redirect(url_for('admin_users'))
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        flash(f'✓ Rolle von {user.username} von "{old_role}" zu "{new_role}" geändert.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
    @login_required
    def admin_toggle_user_status(user_id):
        if current_user.role != 'admin':
            flash('Zugriff verweigert.', 'error')
            return redirect(url_for('admin'))
        
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            flash('Sie können Ihren eigenen Account nicht deaktivieren.', 'error')
            return redirect(url_for('admin_users'))
        
        user.status = 'inactive' if user.status == 'active' else 'active'
        db.session.commit()
        
        status_text = 'aktiviert' if user.status == 'active' else 'deaktiviert'
        flash(f'✓ User {user.username} wurde {status_text}.', 'success')
        return redirect(url_for('admin_users'))

    return app
