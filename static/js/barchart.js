const Chart = function (parent, data, chart_config) {
    function config(chart_config) {
        /* valid parameters
        const valid = {
            barmode: ["stacked", "grouped"],
            type: ["bar", "line", "scatter"],
            orient: ["h", "v"],
            legend: ["show", "hide"],
        };
        */
        const config_default = {
            style: {
                type: chart_config?.style?.type || "bar",
                barmode: chart_config?.style?.barmode || "stacked",
                orient: "v",
                canvas: {
                    width: chart_config?.style?.width || 200,
                    height: chart_config?.style?.height || 300,
                },
                margin: { top: 10, right: 30, bottom: 20, left: 50 },
                legend: { position: "right", orient: "v", translate_x: 0, translate_y: 0, width: 0 }, //left,right,top,bottom,none
            },
            figure: { color: chart_config.color || {} }, //defined in setColors},
            piston: { name: chart_config?.piston?.name || null, fill: chart_config?.piston?.fill || null },
            marker: { name: chart_config?.marker?.name || null, fill: chart_config?.marker?.fill || null },
        };
        chart_config.figure = config_default.figure;
        chart_config.figure.yGroupName = Object.keys(data[0]).slice(1);
        chart_config.style = config_default.style;
        chart_config.style.type = chart_config?.style?.type || config_default.style.type;
        chart_config.style.barmode = chart_config?.style?.barmode || config_default.style.barmode;
        chart_config.style.orientation = chart_config?.style?.orientation || config_default.style.orient;

        chart_config.threshold = chart_config?.threshold || config_default.threshold;
        chart_config.piston = config_default.piston;
        chart_config.marker = chart_config?.marker || config_default.marker;

        switch (config_default.style.legend.position) {
            case null:
                config_default.style.legend.width = 0;
            case "right":
                config_default.style.legend.translate_x =
                    config_default.style.margin.left + config_default.style.canvas.width;
        }
        switch (chart_config.style.type) {
            case "line":
                chart_config.style.barmode = null;
                chart_config.piston = undefined;
                chart_config.marker = undefined;
        }
        chart_config.style.chart_width =
            config_default.style.margin.left +
            config_default.style.margin.right +
            config_default.style.legend.width +
            config_default.style.canvas.width;
        chart_config.style.chart_height =
            config_default.style.margin.top +
            config_default.style.margin.bottom +
            config_default.style.canvas.height;
    }

    function configData() {
        data.piston = null;
        data.marker = null;
        data.stacked = null;
        data.groups = data.columns.slice(1);
        data.groupName = Object.keys(data[0])[0]; //For the X axis
        if (chart_config?.piston?.name) {
            const piston_name = chart_config.piston.name;
            data.piston = data.map((d) => d[piston_name]);
            data.columns = data.columns.filter((e) => e != piston_name);
            data.map((e) => delete e[piston_name]); //remove piston data
            data.groups.splice(data.groups.indexOf(piston_name), 1); //remove piston name
        }
        if (chart_config?.marker?.name) {
            const marker_name = chart_config.marker.name;
            data.marker = data.map((d) => d[marker_name]);
            data.columns = data.columns.filter((e) => e != marker_name);
            data.map((e) => delete e[marker_name]);
            data.groups.splice(data.groups.indexOf(marker_name), 1);
        }
        if (chart_config.style.barmode == "stacked") {
            data.stacked = d3.stack().keys(data.groups)(data);
        }
    }

    function drawPiston() {
        if (chart_config?.piston?.name && chart_config.style?.barmode == "stacked") {
            svg.append("g")
                .attr("class", "piston")
                .selectAll("g")
                .data(data.piston)
                .join("rect")
                .attr("fill", chart_config.piston.fill)
                .attr("x", (d, i) => {
                    let _x = chart_config.figure.xScale(data[i][data.groupName]);
                    return _x + chart_config.figure.xScale.bandwidth() * (3 / 8);
                })
                .attr("y", (d) => chart_config.figure.yScale(d))
                .attr("height", (d) => chart_config.style.canvas.height - chart_config.figure.yScale(d))
                .attr("width", chart_config.figure.xScale.bandwidth() / 4);
        }
    }

    function drawMarker() {
        if (chart_config?.marker?.name) {
            const marker = "M-20,0L0,-5L20,0L0,5Z";
            let xTrans = function (i) {
                let _x = chart_config.figure.xScale(data[i][data.groupName]);
                return _x + chart_config.figure.xScale.bandwidth() / 2;
            };
            svg.append("g")
                .attr("class", "markers")
                .selectAll("g")
                .data(data.marker)
                .join("path")
                .attr("fill", chart_config.marker.fill)
                .attr(
                    "transform",
                    (d, i) => "translate(" + xTrans(i) + "," + chart_config.figure.yScale(d) + ")"
                )
                .attr("d", marker);
        }
    }

    function drawThreshold() {
        //Threshold horizontal line
        if (chart_config.threshold) {
            const threshold = svg.append("g");

            threshold
                .attr("class", "threshold")
                .selectAll("g")
                .data(chart_config.threshold)
                .join("line")
                .style("stroke-dasharray", "15, 7")
                .attr("x1", 0)
                .attr("x2", chart_config.style.canvas.width)
                .attr("y2", (d) => chart_config.figure.yScale(d.value))
                .attr("y1", (d) => chart_config.figure.yScale(d.value))
                .attr("stroke", "red")
                .attr("stroke-width", 2);
            threshold
                .selectAll("g")
                .data(chart_config.threshold)
                .join("text")
                .attr("x", 0)
                .attr("y", (d) => chart_config.figure.yScale(d.value) - 5)
                .text(function (d) {
                    return d.name;
                });
        }
    }
    function drawGroupedBarChart() {
        // Another scale for subgroup position?
        const xSubgroup = d3
            .scaleBand()
            .domain(data.groups)
            .range([0, chart_config.figure.xScale.bandwidth()])
            .padding([0.05]);
        chart_config.figure.yScale
            .domain([0, chart_config.figure.yMax])
            .range([chart_config.style.canvas.height, 0]);

        svg.append("g")
            .selectAll("g")
            .data(data)
            .join("g")
            .attr("transform", (d) => `translate(${chart_config.figure.xScale(d[data.groupName])}, 0)`)
            .selectAll("rect")
            .data(function (d) {
                return data.groups.map(function (key) {
                    return { key: key, value: d[key] };
                });
            })
            .join("rect")
            .attr("x", (d) => xSubgroup(d.key))
            .attr("y", (d) => chart_config.figure.yScale(d.value))
            .attr("width", xSubgroup.bandwidth())
            .attr("height", (d) => chart_config.style.canvas.height - chart_config.figure.yScale(d.value))
            .attr("fill", (d) => chart_config.figure.color[d.key]);
    }

    function drawStackedBarChart() {
        // chart_config.figure.yScale
        //     .domain([0, chart_config.figure.yMax])
        //     .range([chart_config.style.canvas.height, 0]);

        svg.append("g")
            .selectAll("g")
            // Enter in the stack data = loop key per key = group per group
            .data(data.stacked)
            .join("g")
            .attr("fill", (d) => chart_config.figure.color[d.key])
            .selectAll("rect")
            // enter a second time = loop subgroup per subgroup to add all rectangles
            .data((d) => d)
            .join("rect")
            .attr("x", (d) => chart_config.figure.xScale(d.data[data.groupName]))
            .attr("y", (d) => chart_config.figure.yScale(d[1]))
            .attr("height", (d) => chart_config.figure.yScale(d[0]) - chart_config.figure.yScale(d[1]))
            .attr("width", chart_config.figure.xScale.bandwidth());
    }
    function drawLineChart() {
        const line_keys = Object.keys(data[0]).slice(1);
        for (let k of line_keys) {
            svg.append("path")
                .data([data])
                .attr("class", `line ${k}`)
                .attr("fill", "none")
                .attr("stroke", chart_config.figure.color[k])
                .attr("stroke-width", 1.5)
                .attr(
                    "d",
                    d3
                        .line()
                        .x((d) => chart_config.figure.xScale(d[data.groupName]))
                        .y((d) => chart_config.figure.yScale(d[k]))
                );
        }
    }
    function setXScale() {
        const cf = chart_config;
        const required_scaleband = ["bar"];
        const required_linear = ["line"];
        const want_scaleband = required_scaleband.includes(cf.style.type);
        const want_linear = required_linear.includes(cf.style.type);

        if (want_scaleband) {
            cf.figure.xDomain = data.map((d) => d[data.groupName]);
            cf.figure.xScale = d3
                .scaleBand()
                .domain(cf.figure.xDomain)
                .range([0, chart_config.style.canvas.width])
                .padding([0.2]);
            cf.figure.formatXtick = false;
        } else if (want_linear) {
            cf.figure.xDomain = d3.extent(data.map((e) => e[data.groupName]));
            if (Object.getPrototypeOf(data[0][data.groupName]) === Date.prototype) {
                cf.figure.xScale = d3.scaleTime();
            } else {
                cf.figure.xScale = d3.scaleLinear();
                cf.figure.formatXtick = true;
            }
            cf.figure.xScale.range([0, chart_config.style.canvas.width]).domain(cf.figure.xDomain);
        }
    }
    function setYScale() {
        //set a yMax and yMin starting point
        if (chart_config.threshold) {
            chart_config.figure.yMax = d3.max(chart_config.threshold.map((e) => e.value));
        } else {
            chart_config.figure.yMax = data[0][chart_config.figure.yGroupName[0]];
        }
        if (data.piston) {
            chart_config.figure.yMax = Math.max(chart_config.figure.yMax, d3.max(data.piston));
        }
        if (data.marker) {
            chart_config.figure.yMax = Math.max(chart_config.figure.yMax, d3.max(data.marker));
        }
        chart_config.figure.yMin = chart_config.figure.yMax;
        if (chart_config.style.barmode == "stacked") {
            chart_config.figure.yMax = d3.max(data, (d) => {
                let val = 0;
                for (let k of data.groups) {
                    val += parseInt(d[k]);
                }
                return Math.max(chart_config.figure.yMax, val);
            });
        } else {
            for (let k of chart_config.figure.yGroupName) {
                chart_config.figure.yMax = Math.max(
                    chart_config.figure.yMax,
                    d3.max(data.map((d) => parseFloat(d[k] || 0)))
                );
                chart_config.figure.yMin = Math.min(
                    chart_config.figure.yMin,
                    d3.min(data.map((d) => parseFloat(d[k] || 0)))
                );
            }
        }
        chart_config.figure.yMin = chart_config.figure.yMin < 0 ? Math.floor(chart_config.figure.yMin) : 0;
        //Do some rounding up
        chart_config.figure.yMax = Math.ceil(chart_config.figure.yMax);
        chart_config.figure.yMax *= 1.1; //Add 10%

        //apply to scale
        chart_config.figure.yScale = d3.scaleLinear();
        chart_config.figure.yScale
            .domain([chart_config.figure.yMin, chart_config.figure.yMax])
            .range([chart_config.style.canvas.height, 0]);
    }

    function drawYAxis() {
        svg.append("g")
            .attr("class", "yaxis")
            .call(d3.axisLeft(chart_config.figure.yScale).tickSize(-chart_config.style.canvas.width, 2, 20));
    }

    function drawXaxis() {
        let ax = d3.axisBottom(chart_config.figure.xScale).tickSize(5);
        if (chart_config.figure.formatXtick) {
            ax.tickFormat(d3.format(".0f"));
        }
        svg.append("g")
            .attr("class", "xaxis")
            .attr("transform", `translate(0, ${chart_config.style.canvas.height})`)
            .call(ax);
    }
    function setColors() {
        let i = 0;
        for (const s of chart_config.figure.yGroupName) {
            try {
                if (Object.keys(chart_config.figure.color).indexOf(s) == -1) {
                    // chart_config.figure.color[s] = d3.schemeCategory10[i++];
                    chart_config.figure.color[s] = d3.schemeTableau10[i++];
                }
            } catch {}
        }
        if (chart_config?.piston?.fill) {
            chart_config.figure.color[chart_config.piston.name] = chart_config.piston.fill;
        }
        if (chart_config?.marker?.fill) {
            chart_config.figure.color[chart_config.marker.name] = chart_config.marker.fill;
        }
    }
    function Legend() {
        const legendcontainer = svg
            .append("g")
            .attr("class", "legendcontainer")
            .attr("transform", "translate(" + chart_config.style.legend.translate_x + ",0)");
        const legendRectSize = 18;
        const legendSpacing = 4;
        const legend = legendcontainer
            .selectAll(".legenditem")
            .data(chart_config.figure.yGroupName)
            .enter()
            .append("g")
            .attr("class", "legenditem");
        if (chart_config.legend.orient == "v") {
            legend.attr("transform", function (d, i) {
                let height = legendRectSize + legendSpacing;
                let horz = -2 * legendRectSize;
                let vert = i * height;
                return "translate(" + horz + "," + vert + ")";
            });
        } else if (chart_config.legend.orient == "h") {
            legend.attr("transform", function (d, i) {
                let height = legendRectSize + legendSpacing;
                let offset = (height * chart_config.figure.yGroupName.length) / 2;
                let horz = legendRectSize + offset;
                return "translate(" + i * horz + "," + 0 + ")";
            });
        }
        legend
            .append("rect")
            .attr("width", legendRectSize)
            .attr("height", legendRectSize)
            .style("fill", (d) => chart_config.figure.color[d])
            .style("stroke", data.color);
        let tt = legend
            .append("text")
            .attr("x", legendRectSize + legendSpacing)
            .attr("y", legendRectSize - legendSpacing)
            .text(function (d) {
                return d;
            });
        // console.log(tt.getBBox());
    }

    function drawSvgContainer(parent) {
        if (!document.getElementById(parent)) {
            throw `Chart parent <${parent}> does not exist`;
        }
        svg = d3
            .select("#" + parent)
            .append("svg")
            .attr("width", chart_config.style.chart_width)
            .attr("height", chart_config.style.chart_height)
            .append("g")
            .attr("class", "figure")
            .attr(
                "transform",
                `translate(${chart_config.style.margin.left},${chart_config.style.margin.top})`
            );

        //Put a rectangle in the figure so we can set a background
        svg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", chart_config.style.canvas.width)
            .attr("height", chart_config.style.canvas.height)
            .attr("class", "canvas");
    }

    let svg = null;

    config(chart_config);
    configData();
    setColors();
    drawSvgContainer(parent);
    setYScale();
    setXScale();
    drawXaxis();
    drawYAxis();

    if (chart_config.style.type == "bar") {
        if (chart_config.style.barmode == "grouped") {
            drawGroupedBarChart();
        } else if (chart_config.style.barmode == "stacked") {
            drawStackedBarChart();
        }
    } else if (chart_config.style.type == "line") {
        drawLineChart();
    }

    drawThreshold();
    drawPiston();
    drawMarker();

    //Legend
    if (chart_config.legend.visibility === "show") {
        Legend();
    }
};

const ChartHandler = {
    max_legend_width: function () {
        const legend_items = document.querySelectorAll(".legenditem");
        let max_width = 0;
        for (let i of legend_items) {
            max_width = Math.max(max_width, i.getBBox().width);
        }
        return max_width;
    },
    ajust_chart_width: function () {
        const mw = this.max_legend_width();
        const charts = document.querySelectorAll("svg");
        for (let c of charts) {
            c.setAttribute("width", mw + parseFloat(c.getAttribute("width")));
        }
    },
};
export { Chart, ChartHandler };
