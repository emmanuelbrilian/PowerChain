import logging
from flask import Blueprint, flash, redirect, render_template, request

from notification.model import abort_purchase_order_notifications, get_notification_by_id, get_pending_notifications_by_seller, save_notification
from purchase_order.model import PurchaseOrder, get_po_by_id, save_po
from purchase_order.service import select_candidates_and_send_notification
from util.session import get_active_user, is_logged_in
from energy_transfer.model import EnergyTransfer, send_energy_transfer_request

__LOG = logging.getLogger("NotificationService")

notification_service = Blueprint(
    "notification", __name__, template_folder="../templates"
)


@notification_service.route("/notifications_seller", methods=["GET"])
@is_logged_in
def notifications_seller():
    active_user = get_active_user()
    notifications = get_pending_notifications_by_seller(active_user.id)
    return render_template("notifications_seller.html", notifications=notifications)


@notification_service.route("/purchase-requests", methods=["POST"])
@is_logged_in
def decline_request():
    notification_id = request.form["notification_id"]
    purchase_id = request.form["purchase_id"]
    seller_id = request.form["seller_id"]

    notification = get_notification_by_id(notification_id)
    purchase_order = get_po_by_id(purchase_id)

    if "approve" in request.form:
        notification.status = "APPROVED"
        save_notification(notification)

        # TODO create/upload smart contract

        energy_transfer = EnergyTransfer(
            sender=notification.seller_id,
            receiver=purchase_order.buyer_id,
            transfer_amount=notification.requested_energy,
            purchase_id=purchase_id,
        )
        send_energy_transfer_request(energy_transfer)

    elif "decline" in request.form:
        notification.status = "DECLINED"
        save_notification(notification)


        purchase_order.decline_candidate(seller_id)
        try:
            __recalculate_candidates(purchase_order)
        except Exception as e:
            __LOG.debug(f"Error: {e}")
            abort_purchase_order_notifications(purchase_id)
            purchase_order.status = "NO SELLER"

        save_po(purchase_order)

    flash("Response accepted", "success")
    return redirect("/notifications_seller")


def __recalculate_candidates(purchase_order):
    select_candidates_and_send_notification(purchase_order)
