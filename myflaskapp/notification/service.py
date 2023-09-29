from curses import flash
from flask import Blueprint, redirect, render_template, request, url_for
from myflaskapp.notification.model import Notification
from myflaskapp.purchase_order.model import PurchaseOrder

from myflaskapp.util.session import get_active_user, is_logged_in


notification_service = Blueprint(
    "notification", __name__, template_folder="../templates"
)


@notification_service.route("/notifications_seller", methods=["GET"])
@is_logged_in
def notifications_seller():
    active_user = get_active_user()
    notifications = Notification.get_pending_notifications_by_seller(active_user.id)
    return render_template("notifications_seller.html", notifications=notifications)


@notification_service.route("/purchase-requests", methods=["POST"])
@is_logged_in
def decline_request():
    notification_id = request.form["notification_id"]
    purchase_id = request.form["purchase_id"]
    seller_id = request.form["seller_id"]

    notification = Notification.get_by_id(notification_id)

    if "approve" in request.form:
        notification.status = "APPROVED"
        notification.save()

        PurchaseOrder.update_candidate_approve_request(purchase_id, seller_id)
        flash("Notification approved successfully", "success")

        # TODO do energy transfer
        # TODO do transaction to ether

    elif "decline" in request.form:
        notification.status = "DECLINED"
        notification.save()

        PurchaseOrder.update_candidate_decline_request(purchase_id, seller_id)
        flash("Notification declined successfully", "success")

        # TODO re-calculate candidates

    return redirect(url_for("notifications_seller"))
