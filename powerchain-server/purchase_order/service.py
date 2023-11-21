import logging

from flask import Blueprint, flash, redirect, render_template, request

from notification.model import (
    Notification,
    get_pending_notification_by_purchase_and_seller,
    save_notification,
)
from purchase_order.model import PurchaseOrder, save_po
from user.model import get_other_users_with_available_energy
from util.session import get_active_user, is_logged_in

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
        save_po(purchase_order)
        flash("No available candidates", "error")
        return redirect("/dashboard")

    purchase_order.sortCandidatesByDistance(peers)

    if purchase_order.isTotalEnergySufficient():
        purchase_order.status = "NO ENERGY"
        save_po(purchase_order)
        flash("Requested amount cannot be fulfilled", "danger")
        return render_template("purchase.html")

    purchase_order.decideProviderType()
    save_po(purchase_order)

    select_candidates_and_send_notification(purchase_order)
    save_po(purchase_order)

    flash("Your order is being processed", "success")
    return redirect("/dashboard")


@purchase_order_service.route("/purchase", methods=["GET"])
@is_logged_in
def open_purchase_page():
    return render_template("purchase.html")


def select_candidates_and_send_notification(purchase_order: PurchaseOrder):
    if purchase_order.isSingleProvider():
        selected_candidate = purchase_order.select_single_provider_candidate()
        notification = Notification(
            purchase_id=str(purchase_order.id),
            buyer_username=purchase_order.buyer_username,
            seller_id=selected_candidate.seller_id,
            seller_username=selected_candidate.seller_username,
            requested_energy=selected_candidate.requested_energy,
        )
        save_notification(notification)
    else:
        selected_candidates = purchase_order.select_multiple_provider_candidates()
        for sc in selected_candidates:
            notification = get_pending_notification_by_purchase_and_seller(
                purchase_order.id, sc.seller_id
            )
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
            save_notification(notification)
