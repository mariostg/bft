[1mdiff --git a/reports/capitalforecasting.py b/reports/capitalforecasting.py[m
[1mindex f13bc55..cdb685e 100644[m
[1m--- a/reports/capitalforecasting.py[m
[1m+++ b/reports/capitalforecasting.py[m
[36m@@ -1,4 +1,4 @@[m
[31m-from django.db.models import Sum[m
[32m+[m[32mfrom django.db.models import Sum,QuerySet[m
 from costcenter.models import ([m
     CapitalInYear,[m
     CapitalProject,[m
[36m@@ -36,7 +36,7 @@[m [mclass HistoricalOutlookReport(CapitalReport):[m
         super().__init__(fund, capital_project, fy)[m
         self.years = list(range(self.fy - 4, self.fy + 1))[m
 [m
[31m-    def dataset(self):[m
[32m+[m[32m    def dataset(self)->dict[QuerySet]:[m
         in_year = CapitalInYear.objects.filter([m
             fund=self.fund, capital_project=self.capital_project, fy__in=self.years[m
         ).values("fy", "quarter", "mle")[m
[36m@@ -49,7 +49,7 @@[m [mclass HistoricalOutlookReport(CapitalReport):[m
 [m
         return dict(in_year=in_year, new_year=new_year, year_end=year_end)[m
 [m
[31m-    def dataframe(self):[m
[32m+[m[32m    def dataframe(self)->int:[m
         """Create a dataframe of annual data, one row per year for given project and fund"""[m
 [m
         data = self.dataset()[m
[36m@@ -82,17 +82,20 @@[m [mclass HistoricalOutlookReport(CapitalReport):[m
                 df = df.merge(df_q4, how="left", on="fy")[m
             else:[m
                 df["Q4 MLE"] = 0[m
[32m+[m
         if any(data["year_end"]):[m
             df_year_end = pd.DataFrame.from_dict(data["year_end"])[m
[31m-            df = df.merge(df_year_end, how="left", on="fy")[m
[32m+[m[32m            df = df.merge(df_year_end, how="outer", on="fy")[m
 [m
         if any(data["new_year"]):[m
             df_new_year = pd.DataFrame.from_dict(data["new_year"])[m
[31m-            df = df.merge(df_new_year, how="left", on="fy")[m
[32m+[m[32m            print(df_new_year)[m
[32m+[m[32m            df = df.merge(df_new_year, how="outer", on="fy")[m
 [m
         if not df.empty:[m
             self.df = df.rename(columns={"ye_spent": "YE Spent", "initial_allocation": "Initial Allocation"})[m
             self.df = self.df.fillna(0)[m
[32m+[m[32m        return self.df.size[m
 [m
     def to_html(self):[m
         self.dataframe()[m
[36m@@ -114,7 +117,7 @@[m [mclass FEARStatusReport(CapitalReport):[m
         self.quarters = [1, 2, 3, 4][m
         super().__init__(fund, capital_project, fy)[m
 [m
[31m-    def dataset(self):[m
[32m+[m[32m    def dataset(self)->QuerySet:[m
         return ([m
             CapitalInYear.objects.filter(fy=self.fy, fund=self.fund, capital_project=self.capital_project)[m
             .values("capital_project", "fund", "quarter")[m
[36m@@ -131,10 +134,14 @@[m [mclass FEARStatusReport(CapitalReport):[m
             )[m
         )[m
 [m
[31m-    def dataframe(self):[m
[32m+[m[32m    def dataframe(self)->int:[m
         """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""[m
[31m-        self.df = pd.DataFrame.from_dict(self.dataset())[m
[32m+[m[32m        ds=self.dataset()[m
[32m+[m[32m        if not ds.count():[m
[32m+[m[32m            return 0[m
[32m+[m[32m        self.df = pd.DataFrame.from_dict(ds)[m
         self.df.rename(columns={"quarter": "Quarters"}, inplace=True)[m
[32m+[m[32m        return self.df.size[m
 [m
     def to_html(self):[m
         self.dataframe()[m
[36m@@ -210,7 +217,7 @@[m [mclass EstimateReport(CapitalReport):[m
 [m
         super().__init__(fund, capital_project, fy)[m
 [m
[31m-    def dataset(self):[m
[32m+[m[32m    def dataset(self)->QuerySet:[m
         return ([m
             CapitalInYear.objects.filter(fy=self.fy, fund=self.fund, capital_project=self.capital_project)[m
             .values([m
[36m@@ -235,14 +242,18 @@[m [mclass EstimateReport(CapitalReport):[m
             )[m
         )[m
 [m
[31m-    def dataframe(self):[m
[31m-        self.df = pd.DataFrame.from_dict(self.dataset()).rename([m
[32m+[m[32m    def dataframe(self)->int:[m
[32m+[m[32m        ds=self.dataset()[m
[32m+[m[32m        if not ds.count():[m
[32m+[m[32m            return 0[m
[32m+[m[32m        self.df = pd.DataFrame.from_dict(ds).rename([m
             columns={[m
                 "capital_project__fundcenter__fundcenter": "Fund Center",[m
                 "capital_project__project_no": "Project No",[m
                 "working_plan": "Working Plan",[m
             }[m
         )[m
[32m+[m[32m        return self.df.size[m
 [m
     def to_html(self):[m
         self.dataframe()[m
[1mdiff --git a/reports/templates/capital-forecasting-estimates.html b/reports/templates/capital-forecasting-estimates.html[m
[1mindex 9af86cb..b8cd2a1 100644[m
[1m--- a/reports/templates/capital-forecasting-estimates.html[m
[1m+++ b/reports/templates/capital-forecasting-estimates.html[m
[36m@@ -3,9 +3,6 @@[m
 {% block title %}Search Capital Forecasting Estimates{% endblock title %}[m
 {% block content %}[m
 <main class='block block--centered'>[m
[31m-    {% if not table %}[m
[31m-    <div class="alert alert--info">There are no data to display</div>[m
[31m-    {% endif %}[m
     <h1>Capital Forecasting Estimates</h1>[m
     {% if form_filter %}[m
     {% include "core/capital-forecasting-filter.html" %}[m
[1mdiff --git a/reports/templates/capital-forecasting-fears.html b/reports/templates/capital-forecasting-fears.html[m
[1mindex f903572..f3113a4 100644[m
[1m--- a/reports/templates/capital-forecasting-fears.html[m
[1m+++ b/reports/templates/capital-forecasting-fears.html[m
[36m@@ -3,10 +3,6 @@[m
 {% block title %}Capital Forecasting FEARS{% endblock title %}[m
 {% block content %}[m
 <main class='block block--centered'>[m
[31m-    {% if not table %}[m
[31m-    <div class="alert alert--info">There are no data to display</div>[m
[31m-    {% endif %}[m
[31m-[m
     <h1>Capital Forecasting FEARS</h1>[m
     {% if form_filter %}[m
     {% include "core/capital-forecasting-filter.html" %}[m
[1mdiff --git a/reports/templates/capital-historical-outlook.html b/reports/templates/capital-historical-outlook.html[m
[1mindex e4b0d3f..f8c13e9 100644[m
[1m--- a/reports/templates/capital-historical-outlook.html[m
[1m+++ b/reports/templates/capital-historical-outlook.html[m
[36m@@ -3,15 +3,10 @@[m
 {% block title %}Capital Historical Outlook{% endblock title %}[m
 {% block content %}[m
 <main class='block block--centered'>[m
[31m-    {% if not table %}[m
[31m-    <div class="alert alert--info">There are no data to display</div>[m
[31m-    {% endif %}[m
[31m-[m
     <h1>Capital Historical Outlook</h1>[m
     {% if form_filter %}[m
     {% include "core/capital-forecasting-filter.html" %}[m
     {% endif %}[m
[31m-[m
 {% autoescape off %}[m
 {{table}}[m
 {% if data|length > 2 %}[m
[1mdiff --git a/reports/views.py b/reports/views.py[m
[1mindex d1b81f0..98dc7f1 100644[m
[1m--- a/reports/views.py[m
[1m+++ b/reports/views.py[m
[36m@@ -240,9 +240,12 @@[m [mdef capital_forecasting_estimates(request):[m
         fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0[m
         estimates = capitalforecasting.EstimateReport(fund, fy, capital_project)[m
         estimates.dataframe()[m
[31m-        estimates.df.quarter="Q"+estimates.df.quarter[m
[31m-        data = estimates.df.to_json(orient="records")[m
[31m-        table = estimates.to_html()[m
[32m+[m[32m        if estimates.df.size:[m
[32m+[m[32m            estimates.df.quarter="Q"+estimates.df.quarter[m
[32m+[m[32m            data = estimates.df.to_json(orient="records")[m
[32m+[m[32m            table = estimates.to_html()[m
[32m+[m[32m        else:[m
[32m+[m[32m            messages.warning(request,"Capital forecasting estimate is empty")[m
     else:[m
         fy = BftStatus.current.fy()[m
 [m
[36m@@ -278,9 +281,13 @@[m [mdef capital_forecasting_fears(request):[m
         fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0[m
         quarterly = capitalforecasting.FEARStatusReport(fund, fy, capital_project)[m
         quarterly.dataframe()[m
[31m-        quarterly.df.Quarters="Q"+quarterly.df.Quarters[m
[31m-        data = quarterly.df.to_json(orient="records")[m
[31m-        table = quarterly.to_html()[m
[32m+[m[32m        if quarterly.df.size:[m
[32m+[m[32m            quarterly.df.Quarters="Q"+quarterly.df.Quarters[m
[32m+[m[32m            data = quarterly.df.to_json(orient="records")[m
[32m+[m[32m            table = quarterly.to_html()[m
[32m+[m[32m        else:[m
[32m+[m[32m            messages.warning(request,"Capital forecasting FEARS is empty")[m
[32m+[m
     else:[m
         fy = BftStatus.current.fy()[m
 [m
[36m@@ -315,8 +322,12 @@[m [mdef capital_historical_outlook(request):[m
         fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0[m
         outlook = capitalforecasting.HistoricalOutlookReport(fund, fy, capital_project)[m
         outlook.dataframe()[m
[31m-        data = outlook.df.to_json(orient="records")[m
[31m-        table = outlook.to_html()[m
[32m+[m[32m        if outlook.df.size:[m
[32m+[m[32m            data = outlook.df.to_json(orient="records")[m
[32m+[m[32m            table = outlook.to_html()[m
[32m+[m[32m        else:[m
[32m+[m[32m            messages.warning(request,"Capital forecasting historical outlook is empty")[m
[32m+[m
     else:[m
         fy = BftStatus.current.fy()[m
 [m
