% Recreate the final protocol-v3 figures from validated UnetStack CSV output.
% Run from the repository root with:
%   matlab -batch "run('analysis/analyze_final_results.m')"

clear; clc; close all;
set(groot, 'defaultFigureColor', 'w', 'defaultAxesColor', 'w', ...
    'defaultAxesXColor', 'k', 'defaultAxesYColor', 'k', ...
    'defaultTextColor', 'k', 'defaultLegendTextColor', 'k');

scriptPath = mfilename('fullpath');
projectRoot = fileparts(fileparts(scriptPath));
summaryDir = fullfile(projectRoot, 'results', 'v3', 'summary');
outputDir = fullfile(projectRoot, 'results', 'v3', 'matlab_figures');
if ~isfolder(outputDir), mkdir(outputDir); end

overallFile = fullfile(summaryDir, 'overall_comparison.csv');
pairedFile = fullfile(summaryDir, 'paired_effects.csv');
depthFile = fullfile(summaryDir, 'depth_effects.csv');
required = {overallFile, pairedFile, depthFile};
for k = 1:numel(required)
    if ~isfile(required{k})
        error('Missing %s. Run analysis/analyze_results.py first.', required{k});
    end
end

overall = readtable(overallFile, TextType='string');
paired = readtable(pairedFile, TextType='string');
depthEffects = readtable(depthFile, TextType='string');

depthOrder = ["depth15", "depth1000"];
depthLabels = {'15 m', '1000 m'};
modeOrder = ["fixed", "proposed"];
modeLabels = {'Fixed 3000 ms', 'Proposed v3'};
colors = [0.00 0.45 0.70; 0.84 0.37 0.00];

throughput = metricMatrix(overall, 'throughput_bps', depthOrder, modeOrder);
pdr = metricMatrix(overall, 'pdr_pct', depthOrder, modeOrder);
loss = metricMatrix(overall, 'packet_loss_pct', depthOrder, modeOrder);
rtt = metricMatrix(overall, 'average_rtt_ms', depthOrder, modeOrder);
timeouts = metricMatrix(overall, 'timeout_ratio_pct', depthOrder, modeOrder);
retryOverhead = metricMatrix(overall, 'retry_overhead_pct', depthOrder, modeOrder);

makeGroupedBar(throughput, depthLabels, modeLabels, colors, ...
    'Useful throughput (bit/s)', 'Final useful throughput', ...
    'Unique delivered payload bits / 180 s; n = 20 paired seeds per bar', ...
    fullfile(outputDir, 'matlab_throughput'));
makeGroupedBar(pdr, depthLabels, modeLabels, colors, ...
    'Packet-delivery ratio (%)', 'Final reliability', ...
    'Unique delivered / unique generated; n = 20 paired seeds per bar', ...
    fullfile(outputDir, 'matlab_pdr'));
makeGroupedBar(loss, depthLabels, modeLabels, colors, ...
    'Confirmed packet loss (%)', 'Confirmed packet loss', ...
    '100 - PDR; lower is better', fullfile(outputDir, 'matlab_packet_loss'));
makeGroupedBar(rtt, depthLabels, modeLabels, colors, ...
    'Average RTT (ms)', 'Average round-trip time', ...
    'ACK-based RTT; lower is better but ACK policy differs by mode', ...
    fullfile(outputDir, 'matlab_average_rtt'));
makeGroupedBar(timeouts, depthLabels, modeLabels, colors, ...
    'Timeout ratio (%)', 'Timeout ratio', ...
    'ACK deadline expirations / ACK-requested originals', ...
    fullfile(outputDir, 'matlab_timeout_ratio'));
makeGroupedBar(retryOverhead, depthLabels, modeLabels, colors, ...
    'Retry DATA attempts / all DATA attempts (%)', 'Bounded retry overhead', ...
    'Fixed has no application retry; proposed retries confirmed missing IDs', ...
    fullfile(outputDir, 'matlab_retry_overhead'));

throughputGain = orderedColumn(paired, 'throughput_change_pct', depthOrder, 'depth_case');
throughputLow = orderedColumn(paired, 'throughput_ci95_low', depthOrder, 'depth_case');
throughputHigh = orderedColumn(paired, 'throughput_ci95_high', depthOrder, 'depth_case');
makeEffectPlot(throughputGain, throughputLow, throughputHigh, depthLabels, ...
    'Throughput change versus fixed (%)', 'Paired throughput improvement', ...
    'Point estimate and paired bootstrap 95% CI; target = +5%', 5, ...
    fullfile(outputDir, 'matlab_throughput_gain'));

pdrGain = orderedColumn(paired, 'pdr_change_pp', depthOrder, 'depth_case');
pdrLow = orderedColumn(paired, 'pdr_ci95_low', depthOrder, 'depth_case');
pdrHigh = orderedColumn(paired, 'pdr_ci95_high', depthOrder, 'depth_case');
makeEffectPlot(pdrGain, pdrLow, pdrHigh, depthLabels, ...
    'PDR change (percentage points)', 'Paired reliability improvement', ...
    'Point estimate and paired bootstrap 95% CI; target = +5 points', 5, ...
    fullfile(outputDir, 'matlab_pdr_gain'));

depthModeOrder = ["fixed", "proposed"];
depthModeLabels = {'Fixed 3000 ms', 'Proposed v3'};
depthChange = orderedColumn(depthEffects, 'throughput_change_bps', depthModeOrder, 'mode');
depthLow = orderedColumn(depthEffects, 'throughput_ci95_low', depthModeOrder, 'mode');
depthHigh = orderedColumn(depthEffects, 'throughput_ci95_high', depthModeOrder, 'mode');
makeEffectPlot(depthChange, depthLow, depthHigh, depthModeLabels, ...
    '1000 m - 15 m throughput (bit/s)', 'Observed depth effect', ...
    'Paired bootstrap 95% CI; an interval crossing zero is inconclusive', 0, ...
    fullfile(outputDir, 'matlab_depth_effect'));

% Compact dashboard for a lab demonstration.
fig = figure(Color='w', Position=[100 100 1120 760]);
t = tiledlayout(fig, 2, 2, TileSpacing='compact', Padding='compact');
dashboardBar(nexttile(t), throughput, depthLabels, modeLabels, colors, 'Throughput (bit/s)');
dashboardBar(nexttile(t), pdr, depthLabels, modeLabels, colors, 'PDR (%)');
dashboardBar(nexttile(t), loss, depthLabels, modeLabels, colors, 'Packet loss (%)');
dashboardBar(nexttile(t), retryOverhead, depthLabels, modeLabels, colors, 'Retry overhead (%)');
title(t, 'Protocol v3 final held-out results (20 paired seeds per depth)', ...
    FontWeight='bold', Color='k');
exportPair(fig, fullfile(outputDir, 'matlab_final_dashboard'));
close(fig);

writetable(overall, fullfile(outputDir, 'matlab_input_overall_comparison.csv'));
writetable(paired, fullfile(outputDir, 'matlab_input_paired_effects.csv'));
writetable(depthEffects, fullfile(outputDir, 'matlab_input_depth_effects.csv'));

fprintf('MATLAB_FINAL_ANALYSIS_COMPLETE %s\n', outputDir);

function values = metricMatrix(tableData, variable, depthOrder, modeOrder)
values = zeros(numel(depthOrder), numel(modeOrder));
for d = 1:numel(depthOrder)
    for m = 1:numel(modeOrder)
        rows = tableData.depth_case == depthOrder(d) & tableData.approach == modeOrder(m);
        if nnz(rows) ~= 1
            error('Expected one row for %s / %s.', depthOrder(d), modeOrder(m));
        end
        values(d,m) = tableData.(variable)(rows);
    end
end
end

function values = orderedColumn(tableData, variable, order, key)
values = zeros(numel(order), 1);
for k = 1:numel(order)
    rows = tableData.(key) == order(k);
    if nnz(rows) ~= 1, error('Expected one row for %s.', order(k)); end
    values(k) = tableData.(variable)(rows);
end
end

function makeGroupedBar(values, labels, legendLabels, palette, yLabelText, titleText, subtitleText, outputBase)
fig = figure(Color='w', Position=[100 100 900 560]);
ax = axes(fig); hold(ax, 'on');
ax.Color = 'w'; ax.XColor = 'k'; ax.YColor = 'k';
b = bar(ax, values, 'grouped');
for k = 1:numel(b)
    b(k).FaceColor = palette(k,:);
    b(k).EdgeColor = [0.15 0.15 0.15];
    b(k).LineWidth = 0.8;
end
set(ax, XTick=1:numel(labels), XTickLabel=labels, FontName='Arial', FontSize=11);
ylabel(ax, yLabelText); xlabel(ax, 'Receiver C depth');
title(ax, titleText, subtitleText, FontWeight='bold');
lgd = legend(ax, legendLabels, Location='northoutside', Orientation='horizontal', Box='off');
lgd.TextColor = 'k';
grid(ax, 'on'); ax.GridAlpha = 0.18; ax.YLim(1) = 0;
for k = 1:numel(b)
    x = b(k).XEndPoints; y = b(k).YEndPoints;
    text(ax, x, y, compose('%.2f', y), HorizontalAlignment='center', ...
        VerticalAlignment='bottom', FontSize=9, FontWeight='bold');
end
ax.YLim(2) = max(ax.YLim(2), max(values, [], 'all') * 1.22 + eps);
exportPair(fig, outputBase); close(fig);
end

function makeEffectPlot(point, low, high, labels, yLabelText, titleText, subtitleText, target, outputBase)
fig = figure(Color='w', Position=[100 100 900 560]);
ax = axes(fig); hold(ax, 'on');
ax.Color = 'w'; ax.XColor = 'k'; ax.YColor = 'k';
errorbar(ax, 1:numel(point), point, point-low, high-point, 'o', ...
    Color=[0.00 0.32 0.55], MarkerFaceColor=[0.00 0.45 0.70], ...
    MarkerSize=9, LineWidth=1.8, CapSize=14);
yline(ax, 0, '-', Color=[0.25 0.25 0.25], LineWidth=1.0);
if target ~= 0
    yline(ax, target, '--', 'Project target', Color=[0.84 0.37 0.00], LineWidth=1.4);
end
set(ax, XTick=1:numel(labels), XTickLabel=labels, XLim=[0.5 numel(labels)+0.5], ...
    FontName='Arial', FontSize=11);
ylabel(ax, yLabelText); title(ax, titleText, subtitleText, FontWeight='bold');
grid(ax, 'on'); ax.GridAlpha = 0.18;
for k = 1:numel(point)
    text(ax, k, high(k), sprintf(' %.2f [%.2f, %.2f]', point(k), low(k), high(k)), ...
        VerticalAlignment='bottom', HorizontalAlignment='center', FontSize=9, FontWeight='bold');
end
span = max(high) - min(low); if span == 0, span = 1; end
ylim(ax, [min([low; 0; target])-0.18*span, max([high; 0; target])+0.28*span]);
exportPair(fig, outputBase); close(fig);
end

function dashboardBar(ax, values, labels, legendLabels, palette, yLabelText)
b = bar(ax, values, 'grouped');
ax.Color = 'w'; ax.XColor = 'k'; ax.YColor = 'k';
for k = 1:numel(b), b(k).FaceColor = palette(k,:); b(k).EdgeColor = [0.15 0.15 0.15]; end
set(ax, XTick=1:numel(labels), XTickLabel=labels, FontName='Arial', FontSize=9);
ylabel(ax, yLabelText); grid(ax, 'on'); ax.GridAlpha = 0.18; ax.YLim(1) = 0;
lgd = legend(ax, legendLabels, Location='northoutside', Orientation='horizontal', Box='off');
lgd.TextColor = 'k'; lgd.FontSize = 8;
end

function exportPair(fig, outputBase)
exportgraphics(fig, outputBase + ".png", Resolution=300, BackgroundColor='white');
exportgraphics(fig, outputBase + ".pdf", ContentType='vector', BackgroundColor='white');
end
