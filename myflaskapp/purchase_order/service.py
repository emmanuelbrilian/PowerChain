import logging

from flask import Blueprint, flash, redirect, render_template, request

from notification.model import Notification
from purchase_order.model import PurchaseOrder
from user.model import User
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
        buyer_coordinate=user.geo_coordinate,
    )

    peers = User.get_other_users_with_available_energy(user.id)
    __LOG.debug(f"Found {len(peers)} available peers")
    purchase_order.sortCandidatesByDistance(peers)

    if purchase_order.isTotalEnergySufficient():
        flash("Requested amount cannot be fulfilled", "danger")
        return render_template("purchase.html")

    purchase_order.decideProviderType()
    purchase_order.save()

    if purchase_order.provider_type == "SINGLE":
        selected_candidate = purchase_order.select_single_provider_candidate()
        purchase_order.save()
        notification = Notification(
            purchase_id=purchase_order.id,
            buyer_username=purchase_order.buyer_username,
            seller_id=selected_candidate.seller_id,
            seller_username=selected_candidate.seller_username,
            energy_requested=selected_candidate.energy_requested,
        )
        notification.save()
    else:
        selected_candidates = purchase_order.select_multiple_provider_candidates()
        purchase_order.save()
        for sc in selected_candidates:
            notification = Notification(
                purchase_id=purchase_order.id,
                buyer_username=purchase_order.buyer_username,
                seller_id=sc.seller_id,
                seller_username=sc.seller_username,
                energy_requested=sc.energy_requested,
            )
            notification.save()

    flash("Your order is being processed", "success")
    return redirect("/dashboard")


@purchase_order_service.route("/purchase", methods=["GET"])
@is_logged_in
def open_purchase_page():
    return render_template("purchase.html")
