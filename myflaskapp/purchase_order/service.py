import logging

from flask import Blueprint, flash, redirect, render_template, request

from notification.model import Notification
from purchase_order.model import PurchaseOrder
from user.model import User, get_other_users_with_available_energy
from util.session import get_active_user, is_logged_in

__LOG = logging.getLogger("PurchaseOrderService")

purchase_order_service = Blueprint(
    "purchase_order", __name__, template_folder="../templates"
)


@purchase_order_service.route("/purchase", methods=["POST"])
@is_logged_in
def purchase():
    user = get_active_user()

    requested_amount = int(request.form["amount"])
    purchase_order = PurchaseOrder(
        requested_amount=requested_amount,
        buyer_id=user.id,
        buyer_username=user.username,
        buyer_coordinates=user.geo_coordinates,
    )

    peers = get_other_users_with_available_energy(user.id)
    if len(peers) <= 0:
        purchase_order.status = "NO SELLER"
        purchase_order.save()
        flash("No available candidates", "error")
        return redirect("/dashboard")

    purchase_order.sortCandidatesByDistance(peers)

    if purchase_order.isTotalEnergySufficient():
        purchase_order.status = "NO ENERGY"
        purchase_order.save()
        flash("Requested amount cannot be fulfilled", "danger")
        return render_template("purchase.html")

    purchase_order.decideProviderType()
    purchase_order.save()

    select_candidates_and_send_notification(purchase_order)
    purchase_order.save()

    flash("Your order is being processed", "success")
    return redirect("/dashboard")


@purchase_order_service.route("/purchase", methods=["GET"])
@is_logged_in
def open_purchase_page():
    return render_template("purchase.html")


def select_candidates_and_send_notification(purchase_order):
    if purchase_order.isSingleProvider():
        selected_candidate = purchase_order.select_single_provider_candidate()
        notification = Notification(
            purchase_id=str(purchase_order.id),
            buyer_username=purchase_order.buyer_username,
            seller_id=selected_candidate.seller_id,
            seller_username=selected_candidate.seller_username,
            requested_energy=selected_candidate.requested_energy,
        )
        notification.save()
    else:
        selected_candidates = purchase_order.select_multiple_provider_candidates()
        for sc in selected_candidates:
            notification = Notification.get_pending_notification_by_purchase_and_seller(purchase_order.id, sc.seller_id)
            if notification is not None:
                notification.requested_energy = sc.requested_energy
            else:
                notification = Notification(
                    purchase_id=str(purchase_order.id),
                    buyer_username=purchase_order.buyer_username,
                    seller_id=sc.seller_id,
                    seller_username=sc.seller_username,
                    requested_energy=sc.requested_energy,
                )
            notification.save()
