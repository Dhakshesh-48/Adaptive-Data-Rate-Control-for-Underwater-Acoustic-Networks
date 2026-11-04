
% Adaptive Data Rate Control for Underwater Networks
% Compare adaptive-rate and fixed-rate experiments.

clear;
clc;
close all;

adaptiveFile = fullfile('results', 'adaptive-first-run.csv');
fixedFile = fullfile('results', 'fixed-first-run.csv');

if ~isfile(adaptiveFile) || ~isfile(fixedFile)
    error('Experiment CSV files not found. Run this script from the 
project root.');
end

A = readtable(adaptiveFile);
F = readtable(fixedFile);

% Calculate summary metrics from event logs.
files = {A, F};
labels = {'Adaptive', 'Fixed'};
n = numel(files);

sent = zeros(n, 1);
acked = zeros(n, 1);
timeouts = zeros(n, 1);
meanRTT = zeros(n, 1);
ackRatio = zeros(n, 1);

for k = 1:n
    T = files{k};

    events = string(T.event);
    isSend = strcmpi(events, 'SEND');
    isAck = strcmpi(events, 'ACK');
    isTimeout = strcmpi(events, 'TIMEOUT');

    sent(k) = sum(isSend);
    acked(k) = sum(isAck);
    timeouts(k) = sum(isTimeout);

    rttValues = T.rtt_ms(isAck & ~isnan(T.rtt_ms));
    if ~isempty(rttValues)
        meanRTT(k) = mean(rttValues);
    end

    if sent(k) > 0
        ackRatio(k) = 100 * acked(k) / sent(k);
    end
end

% Print results.
Results = table( ...
    labels', sent, acked, timeouts, ackRatio, meanRTT, ...
    'VariableNames', {'Mode', 'Sent', 'ACKs', 'Timeouts', ...
                      'ACKSentPercent', 'MeanRTT_ms'});

disp('=== Experiment comparison ===');
disp(Results);

% Figure 1: Summary metrics.
figure('Name', 'Experiment Summary');

subplot(1, 3, 1);
bar(ackRatio);
set(gca, 'XTickLabel', labels);
ylabel('ACKs / sends (%)');
title('ACK-to-send ratio');
grid on;

subplot(1, 3, 2);
bar(meanRTT / 1000);
set(gca, 'XTickLabel', labels);
ylabel('Mean RTT (seconds)');
title('Mean ACK RTT');
grid on;

subplot(1, 3, 3);
bar(timeouts);
set(gca, 'XTickLabel', labels);
ylabel('Timeout events');
title('Recorded timeouts');
grid on;

% Figure 2: Sending interval over elapsed experiment time.
figure('Name', 'Sending Interval');

hold on;
for k = 1:n
    T = files{k};
    events = string(T.event);
    idx = strcmpi(events, 'SEND');

    if any(idx)
        t = T.time_ms(idx);
        interval = T.interval_ms(idx);
        elapsed = (t - t(1)) / 1000;

        plot(elapsed, interval / 1000, ...
            'DisplayName', labels{k});
    end
end
xlabel('Elapsed time within each run (seconds)');
ylabel('Sending interval (seconds)');
title('Sending interval over time');
legend('Location', 'best');
grid on;
hold off;

% Figure 3: RTT of acknowledged packets over elapsed time.
figure('Name', 'ACK Round-Trip Time');

hold on;
for k = 1:n
    T = files{k};
    events = string(T.event);
    idx = strcmpi(events, 'ACK') & ~isnan(T.rtt_ms);

    if any(idx)
        t = T.time_ms(idx);
        rtt = T.rtt_ms(idx);
        elapsed = (t - t(1)) / 1000;

        plot(elapsed, rtt / 1000, '.', ...
            'DisplayName', labels{k});
    end
end
xlabel('Elapsed time from first ACK (seconds)');
ylabel('ACK RTT (seconds)');
title('Round-trip time of acknowledged packets');
legend('Location', 'best');
grid on;
hold off;

