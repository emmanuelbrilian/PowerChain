from bson import ObjectId
from flask import Blueprint, flash, redirect, render_template, request, url_for
from myflaskapp.notification.model import Notification

from myflaskapp.purchase_order.model import PurchaseOrder
from myflaskapp.user.model import User
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
        requested_amount, user.id, user.username, user.geo_coordinate
    )

    peers = User.get_other_users_with_available_energy(user.id)
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
            purchase_order.id,
            purchase_order.buyer_username,
            selected_candidate["user_id"],
            selected_candidate["username"],
            selected_candidate["energy_taken"],
        )
        notification.save()
    else:
        selected_candidates = purchase_order.select_multiple_provider_candidates()
        purchase_order.save()
        for sc in selected_candidates:
            notification = Notification(
                purchase_order.id,
                purchase_order.buyer_username,
                sc["user_id"],
                sc["username"],
                sc["energy_taken"],
            )
            notification.save()

    flash("Your order is being processed", "success")
    return redirect(url_for("dashboard"))


@purchase_order_service.route("/purchase", methods=["GET"])
@is_logged_in
def open_purchase_page():
    return render_template("purchase.html")
