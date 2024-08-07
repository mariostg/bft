from django.urls import path

from bft.views import bft, charges, costcenter, lineitems, users

urlpatterns = [path("", bft.HomeView.as_view(), name="bft")]

urlpatterns += [
    path("bft-status", bft.bft_status, name="bft-status"),
    path("bft-fy-update", bft.bft_fy_update, name="bft-fy-update"),
    path("bft-quarter-update", bft.bft_quarter_update, name="bft-quarter-update"),
    path("bft-period-update", bft.bft_period_update, name="bft-period-update"),
]


urlpatterns += [
    path(
        "charges", charges.cost_center_charge_upload, name="cost-center-charges-upload"
    ),
    path(
        "charges/cc_charge_upload",
        charges.cost_center_charge_upload,
        name="cost-center-charges-upload",
    ),
]

urlpatterns += [
    path("fund/fund-table/", costcenter.fund_page, name="fund-table"),
    path("fund/fund-add/", costcenter.fund_add, name="fund-add"),
    path("fund/fund-update/<int:pk>/", costcenter.fund_update, name="fund-update"),
    path("fund/fund-delete/<int:pk>/", costcenter.fund_delete, name="fund-delete"),
    path("fund/fund-upload", costcenter.fund_upload, name="fund-upload"),
]

urlpatterns += [
    path("source/source-table/", costcenter.source_page, name="source-table"),
    path("source/source-add/", costcenter.source_add, name="source-add"),
    path(
        "source/source-update/<int:pk>/", costcenter.source_update, name="source-update"
    ),
    path(
        "source/source-delete/<int:pk>/", costcenter.source_delete, name="source-delete"
    ),
    path("source/source-upload", costcenter.source_upload, name="source-upload"),
]

urlpatterns += [
    path(
        "fundcenter/fundcenter-table/",
        costcenter.fundcenter_page,
        name="fundcenter-table",
    ),
    path("fundcenter-add/", costcenter.fundcenter_add, name="fundcenter-add"),
    path(
        "fundcenter/fundcenter-update/<int:pk>",
        costcenter.fundcenter_update,
        name="fundcenter-update",
    ),
    path(
        "fundcenter/fundcenter-delete/<int:pk>",
        costcenter.fundcenter_delete,
        name="fundcenter-delete",
    ),
    path(
        "fundcenter/fundcenter-upload",
        costcenter.fundcenter_upload,
        name="fundcenter-upload",
    ),
]

urlpatterns += [
    path(
        "fundcenter/fundcenter-allocation-table/",
        costcenter.fundcenter_allocation_page,
        name="fundcenter-allocation-table",
    ),
    path(
        "fundcenter/fundcenter-allocation-add/",
        costcenter.fundcenter_allocation_add,
        name="fundcenter-allocation-add",
    ),
    path(
        "fundcenter/fundcenter-allocation-update/<int:pk>",
        costcenter.fundcenter_allocation_update,
        name="fundcenter-allocation-update",
    ),
    path(
        "fundcenter/fundcenter-allocation-delete/<int:pk>",
        costcenter.fundcenter_allocation_delete,
        name="fundcenter-allocation-delete",
    ),
    path(
        "fundcenter/fundcenter-allocation-upload",
        costcenter.fundcenter_allocation_upload,
        name="fundcenter-allocation-upload",
    ),
]

urlpatterns += [
    path(
        "costcenter/costcenter-table/",
        costcenter.costcenter_page,
        name="costcenter-table",
    ),
    path(
        "costcenter/costcenter-add/", costcenter.costcenter_add, name="costcenter-add"
    ),
    path(
        "costcenter/costcenter-update/<int:pk>",
        costcenter.costcenter_update,
        name="costcenter-update",
    ),
    path(
        "costcenter/costcenter-delete/<int:pk>",
        costcenter.costcenter_delete,
        name="costcenter-delete",
    ),
    path(
        "costcenter/costcenter-upload",
        costcenter.costcenter_upload,
        name="costcenter-upload",
    ),
]

urlpatterns += [
    path(
        "costcenter/costcenter-allocation-table/",
        costcenter.costcenter_allocation_page,
        name="costcenter-allocation-table",
    ),
    path(
        "costcenter/costcenter-allocation-add/",
        costcenter.costcenter_allocation_add,
        name="costcenter-allocation-add",
    ),
    path(
        "costcenter/costcenter-allocation-update/<int:pk>",
        costcenter.costcenter_allocation_update,
        name="costcenter-allocation-update",
    ),
    path(
        "costcenter/costcenter-allocation-delete/<int:pk>",
        costcenter.costcenter_allocation_delete,
        name="costcenter-allocation-delete",
    ),
    path(
        "costcenter/costcenter-allocation-upload",
        costcenter.costcenter_allocation_upload,
        name="costcenter-allocation-upload",
    ),
]

urlpatterns += [
    path(
        "costcenter/forecast-adjustment-table",
        costcenter.forecast_adjustment_page,
        name="forecast-adjustment-table",
    ),
    path(
        "costcenter/forecast-adjustment-add",
        costcenter.forecast_adjustment_add,
        name="forecast-adjustment-add",
    ),
    path(
        "costcenter/forecast-adjustment-update/<int:pk>",
        costcenter.forecast_adjustment_update,
        name="forecast-adjustment-update",
    ),
    path(
        "forecast-adjustments-delete/<int:pk>",
        costcenter.forecast_adjustment_delete,
        name="forecast-adjustment-delete",
    ),
]

urlpatterns += [
    path(
        "capital-project-table/",
        costcenter.capital_project_page,
        name="capital-project-table",
    ),
    path(
        "capital-project-add/",
        costcenter.capital_project_add,
        name="capital-project-add",
    ),
    path(
        "capital-project-update/<int:pk>",
        costcenter.capital_project_update,
        name="capital-project-update",
    ),
    path(
        "capital-project-delete/<int:pk>",
        costcenter.capital_project_delete,
        name="capital-project-delete",
    ),
    path(
        "capital-project-upload",
        costcenter.capital_project_upload,
        name="capital-project-upload",
    ),
    path(
        "capital-forecasting-new-year-table",
        costcenter.capital_forecasting_new_year_table,
        name="capital-forecasting-new-year-table",
    ),
    path(
        "capital-forecasting-new-year-add",
        costcenter.capital_forecasting_new_year_add,
        name="capital-forecasting-new-year-add",
    ),
    path(
        "capital-forecasting-new-year-update/<int:pk>",
        costcenter.capital_forecasting_new_year_update,
        name="capital-forecasting-new-year-update",
    ),
    path(
        "capital-forecasting-new-year-delete/<int:pk>",
        costcenter.capital_forecasting_new_year_delete,
        name="capital-forecasting-new-year-delete",
    ),
    path(
        "capital-forecasting-in-year-table",
        costcenter.capital_forecasting_in_year_table,
        name="capital-forecasting-in-year-table",
    ),
    path(
        "capital-forecasting-in-year-add",
        costcenter.capital_forecasting_in_year_add,
        name="capital-forecasting-in-year-add",
    ),
    path(
        "capital-forecasting-in-year-update/<int:pk>",
        costcenter.capital_forecasting_in_year_update,
        name="capital-forecasting-in-year-update",
    ),
    path(
        "capital-forecasting-in-year-delete/<int:pk>",
        costcenter.capital_forecasting_in_year_delete,
        name="capital-forecasting-in-year-delete",
    ),
    path(
        "capital-forecasting-year-end-table",
        costcenter.capital_forecasting_year_end_table,
        name="capital-forecasting-year-end-table",
    ),
    path(
        "capital-forecasting-year-end-add",
        costcenter.capital_forecasting_year_end_add,
        name="capital-forecasting-year-end-add",
    ),
    path(
        "capital-forecasting-year-end-update/<int:pk>",
        costcenter.capital_forecasting_year_end_update,
        name="capital-forecasting-year-end-update",
    ),
    path(
        "capital-forecasting-year-end-delete/<int:pk>",
        costcenter.capital_forecasting_year_end_delete,
        name="capital-forecasting-year-end-delete",
    ),
    path(
        "capital-forecasting-new-year-upload",
        costcenter.capital_forecasting_new_year_upload,
        name="capital-forecasting-new-year-upload",
    ),
    path(
        "capital-forecasting-in-year-upload",
        costcenter.capital_forecasting_in_year_upload,
        name="capital-forecasting-in-year-upload",
    ),
    path(
        "capital-forecasting-year-end-upload",
        costcenter.capital_forecasting_year_end_upload,
        name="capital-forecasting-year-end-upload",
    ),
]

urlpatterns += [
    path("", lineitems.lineitem_page, name="lineitem-page"),
    path("lineitem/", lineitems.lineitem_page, name="lineitem-page"),
    path("lineitem/costcenter/<int:pk>/", lineitems.lineitem_page, name="lineitem-page"),
    path("lineitem/delete/<int:pk>", lineitems.line_item_delete, name="line-item-delete"),
    path(
        "fundcenter-lineitem-upload",
        lineitems.fundcenter_lineitem_upload,
        name="fundcenter-lineitem-upload",
    ),
    path(
        "costcenter-lineitem-upload",
        lineitems.costcenter_lineitem_upload,
        name="costcenter-lineitem-upload",
    ),
    path(
        "line_forecast/update/<int:pk>",
        lineitems.line_forecast_update,
        name="line-forecast-update",
    ),
    path(
        "line_forecast/wp/<int:pk>",
        lineitems.line_forecast_to_wp_update,
        name="line-forecast-to-wp-update",
    ),
    path(
        "line_forecast/zero/<int:pk>",
        lineitems.line_forecast_zero_update,
        name="line-forecast-zero-update",
    ),
    path(
        "line-forecast/add/<int:pk>",
        lineitems.line_forecast_add,
        name="line-forecast-add",
    ),
    path(
        "line_forecast/delete/<int:pk>",
        lineitems.line_forecast_delete,
        name="line-forecast-delete",
    ),
    path(
        "document-forecast/<str:docno>",
        lineitems.document_forecast,
        name="document-forecast",
    ),
    path(
        "costcenter-forecast/<int:costcenter_pk>",
        lineitems.costcenter_forecast,
        name="costcenter-forecast",
    ),
]


urlpatterns += [
    path("login/", users.user_login, name="login"),
    path("logout/", users.user_logout, name="logout"),
    path("user-profile/", users.user_profile, name="profile"),
    path("register/", users.register_new_user, name="register"),
    path("user-table/", users.user_page, name="user-table"),
    path("user-add/", users.user_add, name="user-add"),
    path("user-update/<int:pk>", users.user_update, name="user-update"),
    path("user-delete/<int:pk>", users.user_delete, name="user-delete"),
    path(
        "user-password-reset/<int:pk>",
        users.user_password_reset,
        name="user-password-reset",
    ),
]

urlpatterns += [
    path("bookmark/add/<str:bm_page>/", users.bookmark_add, name="bookmark-add"),
    path("bookmark/add/<str:bm_page>/<str:query_string>/", users.bookmark_add, name="bookmark-add"),
    path("bookmark/show/", users.bookmark_show, name="bookmark-show"),
    path("bookmark/delete/<int:pk>", users.bookmark_delete, name="bookmark-delete"),
    path("bookmark/rename/<int:pk>", users.bookmark_rename, name="bookmark-rename"),
]
