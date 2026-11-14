%% CONSTRUIRE_ET_VERIFIER_MODELES
% Script généré automatiquement à partir de la description unique des modèles :
% les positions des blocs sont identiques à celles des schémas du guide.
% Construit mod_am.slx, mod_fm.slx et mod_pm.slx (simulation pure, sans matériel),
% les exécute, ouvre les oscilloscopes et vérifie les sorties.
clear; clc;
ici = fileparts(mfilename('fullpath'));
addpath(fullfile(ici, '..', 'MATLAB', 'outils'));
diary(fullfile(ici, 'journal_matlab.txt'));
nok = 0; ntot = 0;
K = 2001:10000;   % échantillons analysés (régime établi)

%% ===================== Modèle Simulink AM : émetteur, canal et récepteur à détection d'enveloppe =====================
mdl = 'mod_am';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
set_param(mdl, 'SolverType', 'Fixed-step', 'Solver', 'FixedStepDiscrete', 'FixedStep', '5e-06', 'StopTime', '0.05');
hws = get_param(mdl, 'ModelWorkspace');
fs = 200e3;
hws.assignin('fs', 200e3);
hws.assignin('fc', 10e3);
hws.assignin('fm', 1e3);
hws.assignin('m', 0.5);
hws.assignin('phi', 0.7);
hws.assignin('sigma2', 0);
hws.assignin('hpre', lpf_hamming(3e3, fs, 401));
add_block('simulink/Sources/Sine Wave', [mdl '/Message'], 'Position', [40 40 100 90], 'Amplitude', '1', 'Frequency', '2*pi*fm', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Gain', [mdl '/Indice m'], 'Position', [160 40 220 90], 'Gain', 'm');
add_block('simulink/Sources/Constant', [mdl '/Un'], 'Position', [160 117 210 157], 'Value', '1');
add_block('simulink/Math Operations/Sum', [mdl '/Plus 1'], 'Position', [280 85 312 117], 'Inputs', '++');
add_block('simulink/Sources/Sine Wave', [mdl '/Porteuse'], 'Position', [280 166 340 216], 'Amplitude', '1', 'Frequency', '2*pi*fc', 'Phase', 'pi/2+phi', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Product', [mdl '/Modulateur'], 'Position', [400 118 442 174], 'Inputs', '2');
add_block('simulink/Sources/Random Number', [mdl '/Bruit'], 'Position', [400 220 460 270], 'Mean', '0', 'Variance', 'sigma2', 'Seed', '1', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Sum', [mdl '/Canal'], 'Position', [520 175 552 207], 'Inputs', '++');
add_block('simulink/Math Operations/Gain', [mdl '/Oppose'], 'Position', [520 58 580 108], 'Gain', '-1');
add_block('simulink/Signal Routing/Mux', [mdl '/Mux AM'], 'Position', [640 75 650 145], 'Inputs', '3');
add_block('simulink/Sinks/To Workspace', [mdl '/sam'], 'Position', [532 -26 617 12], 'VariableName', 'sam', 'SaveFormat', 'Array');
add_block('simulink/Sources/Sine Wave', [mdl '/OL cos'], 'Position', [40 328 100 378], 'Amplitude', '2', 'Frequency', '2*pi*fc', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Sources/Sine Wave', [mdl '/OL -sin'], 'Position', [40 472 100 522], 'Amplitude', '-2', 'Frequency', '2*pi*fc', 'Phase', '0', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur I'], 'Position', [160 352 202 408], 'Inputs', '2');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur Q'], 'Position', [160 442 202 498], 'Inputs', '2');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre I'], 'Position', [280 355 350 405], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre Q'], 'Position', [280 445 350 495], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Math Operations/Real-Imag to Complex', [mdl '/Re-Im vers complexe'], 'Position', [400 368 460 428], 'Input', 'Real and imag');
add_block('simulink/Math Operations/Complex to Magnitude-Angle', [mdl '/Enveloppe'], 'Position', [520 373 580 423], 'Output', 'Magnitude');
add_block('simulink/Sinks/To Workspace', [mdl '/env'], 'Position', [760 451 845 489], 'VariableName', 'env', 'SaveFormat', 'Array');
add_block('simulink/Sinks/Scope', [mdl '/Scope'], 'Position', [760 144 810 220], 'NumInputPorts', '4');
add_line(mdl, 'Message/1', 'Indice m/1', 'autorouting', 'on');
add_line(mdl, 'Indice m/1', 'Plus 1/1', 'autorouting', 'on');
add_line(mdl, 'Un/1', 'Plus 1/2', 'autorouting', 'on');
add_line(mdl, 'Plus 1/1', 'Modulateur/1', 'autorouting', 'on');
add_line(mdl, 'Porteuse/1', 'Modulateur/2', 'autorouting', 'on');
add_line(mdl, 'Modulateur/1', 'Canal/1', 'autorouting', 'on');
add_line(mdl, 'Bruit/1', 'Canal/2', 'autorouting', 'on');
add_line(mdl, 'Plus 1/1', 'Oppose/1', 'autorouting', 'on');
add_line(mdl, 'Modulateur/1', 'Mux AM/1', 'autorouting', 'on');
add_line(mdl, 'Plus 1/1', 'Mux AM/2', 'autorouting', 'on');
add_line(mdl, 'Oppose/1', 'Mux AM/3', 'autorouting', 'on');
add_line(mdl, 'Modulateur/1', 'sam/1', 'autorouting', 'on');
add_line(mdl, 'OL cos/1', 'Melangeur I/1', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur I/2', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur Q/1', 'autorouting', 'on');
add_line(mdl, 'OL -sin/1', 'Melangeur Q/2', 'autorouting', 'on');
add_line(mdl, 'Melangeur I/1', 'Filtre I/1', 'autorouting', 'on');
add_line(mdl, 'Melangeur Q/1', 'Filtre Q/1', 'autorouting', 'on');
add_line(mdl, 'Filtre I/1', 'Re-Im vers complexe/1', 'autorouting', 'on');
add_line(mdl, 'Filtre Q/1', 'Re-Im vers complexe/2', 'autorouting', 'on');
add_line(mdl, 'Re-Im vers complexe/1', 'Enveloppe/1', 'autorouting', 'on');
add_line(mdl, 'Enveloppe/1', 'env/1', 'autorouting', 'on');
add_line(mdl, 'Message/1', 'Scope/1', 'autorouting', 'on');
add_line(mdl, 'Mux AM/1', 'Scope/2', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Scope/3', 'autorouting', 'on');
add_line(mdl, 'Enveloppe/1', 'Scope/4', 'autorouting', 'on');
save_system(mdl, fullfile(ici, [mdl '.slx']));
if usejava('desktop'), open_system(mdl); end
print(['-s' mdl], '-dpng', '-r150', fullfile(ici, [mdl '_schema.png']));   % schéma bloc exporté par Simulink
hws.assignin('sigma2', 0); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');
% signal émis : enveloppe 1 +/- m et raies à fc et fc +/- fm
s = so.get('sam'); s = s(K); a = abs(signal_analytique(s)); a = a(500:end-500);
ntot = ntot+1; nok = nok + verifier('AM emis : enveloppe maximale', max(a), 1.5, 0.01);
ntot = ntot+1; nok = nok + verifier('AM emis : enveloppe minimale', min(a), 0.5, 0.01);
S = abs(fft(s(:).*hann_(numel(s)))); f = (0:numel(s)-1)*200e3/numel(s); r = @(f0) 20*log10(S(round(f0*numel(s)/200e3)+1)/max(S));
ntot = ntot+1; nok = nok + verifier('AM emis : bande laterale 11 kHz (dB / porteuse)', r(11e3), -12.04, 0.1);
y = so.get('env'); y = y(K) - mean(y(K)); r0 = rsb_tonalite(y, 1e3, 200e3);
ntot = ntot+1; nok = nok + (r0 > 40); fprintf('AM : RSB sans bruit = %.1f dB (> 40 dB attendu)\n', r0);
hws.assignin('sigma2', 0.02); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');   % même modèle, canal bruité
y = so.get('env'); y = y(2001:10000) - mean(y(2001:10000));
fprintf('     AM : RSB de sortie avec sigma2 = 0.02 : %.1f dB (reference : 20.9 dB)\n', rsb_tonalite(y, 1e3, 200e3));
if usejava('desktop'), open_system([mdl '/Scope']); end   % oscilloscope de la dernière simulation (canal bruité)
f = figure('Visible', 'off', 'Position', [0 0 900 600]); t = (0:numel(so.get('sam'))-1)/200e3*1e3; k = t >= 5 & t <= 8;
e = so.get('env'); s = so.get('sam'); subplot(2,1,1); plot(t(k), s(k)); title('mod\_am : signal AM emis s(t)'); grid on;
subplot(2,1,2); plot(t(k), e(k)); title('Enveloppe demodulee (sigma2 = 0,02)'); xlabel('Temps (ms)'); grid on;
exportgraphics(f, fullfile(ici, 'mod_am_resultat.png')); close(f);
save_system(mdl);

%% ===================== Modèle Simulink FM : intégrateur, porteuse, canal et discriminateur I/Q =====================
mdl = 'mod_fm';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
set_param(mdl, 'SolverType', 'Fixed-step', 'Solver', 'FixedStepDiscrete', 'FixedStep', '5e-06', 'StopTime', '0.05');
hws = get_param(mdl, 'ModelWorkspace');
fs = 200e3;
hws.assignin('fs', 200e3);
hws.assignin('fc', 10e3);
hws.assignin('fm', 1e3);
hws.assignin('df', 5e3);
hws.assignin('phi', 0.7);
hws.assignin('sigma2', 0);
hws.assignin('hpre', lpf_hamming(8e3, fs, 201));
hws.assignin('hpost', lpf_hamming(4e3, fs, 201));
add_block('simulink/Sources/Sine Wave', [mdl '/Message'], 'Position', [40 40 100 90], 'Amplitude', '1', 'Frequency', '2*pi*fm', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Gain', [mdl '/2 pi df'], 'Position', [160 40 220 90], 'Gain', '2*pi*df');
add_block('simulink/Discrete/Discrete-Time Integrator', [mdl '/Integrateur'], 'Position', [280 38 350 92], 'gainval', '1', 'IntegratorMethod', 'Integration: Forward Euler', 'SampleTime', '1/fs');
add_block('simulink/Sources/Digital Clock', [mdl '/Horloge'], 'Position', [40 132 100 178], 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Gain', [mdl '/2 pi fc'], 'Position', [160 130 220 180], 'Gain', '2*pi*fc');
add_block('simulink/Sources/Constant', [mdl '/phi'], 'Position', [160 207 210 247], 'Value', 'phi');
add_block('simulink/Math Operations/Sum', [mdl '/Phase porteuse'], 'Position', [280 175 312 207], 'Inputs', '++');
add_block('simulink/Math Operations/Sum', [mdl '/Phase totale'], 'Position', [520 103 552 135], 'Inputs', '++');
add_block('simulink/Math Operations/Trigonometric Function', [mdl '/cos'], 'Position', [640 94 702 144], 'Operator', 'cos');
add_block('simulink/Sources/Random Number', [mdl '/Bruit'], 'Position', [640 184 700 234], 'Mean', '0', 'Variance', 'sigma2', 'Seed', '1', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Sum', [mdl '/Canal'], 'Position', [760 139 792 171], 'Inputs', '++');
add_block('simulink/Sinks/To Workspace', [mdl '/sfm'], 'Position', [880 46 965 84], 'VariableName', 'sfm', 'SaveFormat', 'Array');
add_block('simulink/Sources/Sine Wave', [mdl '/OL cos'], 'Position', [40 328 100 378], 'Amplitude', '2', 'Frequency', '2*pi*fc', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Sources/Sine Wave', [mdl '/OL -sin'], 'Position', [40 472 100 522], 'Amplitude', '-2', 'Frequency', '2*pi*fc', 'Phase', '0', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur I'], 'Position', [160 352 202 408], 'Inputs', '2');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur Q'], 'Position', [160 442 202 498], 'Inputs', '2');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre I'], 'Position', [280 355 350 405], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre Q'], 'Position', [280 445 350 495], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Math Operations/Real-Imag to Complex', [mdl '/Re-Im vers complexe'], 'Position', [400 368 460 428], 'Input', 'Real and imag');
add_block('simulink/Discrete/Unit Delay', [mdl '/Retard z^-1'], 'Position', [520 445 570 495]);
add_block('simulink/Math Operations/Math Function', [mdl '/conj'], 'Position', [640 448 700 492], 'Operator', 'conj');
add_block('simulink/Math Operations/Product', [mdl '/z.conj(z1)'], 'Position', [760 370 802 426], 'Inputs', '2');
add_block('simulink/Math Operations/Complex to Magnitude-Angle', [mdl '/arg'], 'Position', [880 373 940 423], 'Output', 'Angle');
add_block('simulink/Math Operations/Gain', [mdl '/fs//(2 pi)'], 'Position', [1000 373 1060 423], 'Gain', 'fs/(2*pi)');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre de sortie'], 'Position', [1120 373 1190 423], 'Numerator', 'hpost', 'Denominator', '1');
add_block('simulink/Sinks/To Workspace', [mdl '/yfm'], 'Position', [1240 451 1325 489], 'VariableName', 'yfm', 'SaveFormat', 'Array');
add_block('simulink/Sinks/Scope', [mdl '/Scope'], 'Position', [1240 154 1290 228], 'NumInputPorts', '3');
add_line(mdl, 'Message/1', '2 pi df/1', 'autorouting', 'on');
add_line(mdl, '2 pi df/1', 'Integrateur/1', 'autorouting', 'on');
add_line(mdl, 'Horloge/1', '2 pi fc/1', 'autorouting', 'on');
add_line(mdl, '2 pi fc/1', 'Phase porteuse/1', 'autorouting', 'on');
add_line(mdl, 'phi/1', 'Phase porteuse/2', 'autorouting', 'on');
add_line(mdl, 'Integrateur/1', 'Phase totale/1', 'autorouting', 'on');
add_line(mdl, 'Phase porteuse/1', 'Phase totale/2', 'autorouting', 'on');
add_line(mdl, 'Phase totale/1', 'cos/1', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'Canal/1', 'autorouting', 'on');
add_line(mdl, 'Bruit/1', 'Canal/2', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'sfm/1', 'autorouting', 'on');
add_line(mdl, 'OL cos/1', 'Melangeur I/1', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur I/2', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur Q/1', 'autorouting', 'on');
add_line(mdl, 'OL -sin/1', 'Melangeur Q/2', 'autorouting', 'on');
add_line(mdl, 'Melangeur I/1', 'Filtre I/1', 'autorouting', 'on');
add_line(mdl, 'Melangeur Q/1', 'Filtre Q/1', 'autorouting', 'on');
add_line(mdl, 'Filtre I/1', 'Re-Im vers complexe/1', 'autorouting', 'on');
add_line(mdl, 'Filtre Q/1', 'Re-Im vers complexe/2', 'autorouting', 'on');
add_line(mdl, 'Re-Im vers complexe/1', 'Retard z^-1/1', 'autorouting', 'on');
add_line(mdl, 'Retard z^-1/1', 'conj/1', 'autorouting', 'on');
add_line(mdl, 'Re-Im vers complexe/1', 'z.conj(z1)/1', 'autorouting', 'on');
add_line(mdl, 'conj/1', 'z.conj(z1)/2', 'autorouting', 'on');
add_line(mdl, 'z.conj(z1)/1', 'arg/1', 'autorouting', 'on');
add_line(mdl, 'arg/1', 'fs//(2 pi)/1', 'autorouting', 'on');
add_line(mdl, 'fs//(2 pi)/1', 'Filtre de sortie/1', 'autorouting', 'on');
add_line(mdl, 'Filtre de sortie/1', 'yfm/1', 'autorouting', 'on');
add_line(mdl, 'Message/1', 'Scope/1', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'Scope/2', 'autorouting', 'on');
add_line(mdl, 'Filtre de sortie/1', 'Scope/3', 'autorouting', 'on');
save_system(mdl, fullfile(ici, [mdl '.slx']));
if usejava('desktop'), open_system(mdl); end
print(['-s' mdl], '-dpng', '-r150', fullfile(ici, [mdl '_schema.png']));   % schéma bloc exporté par Simulink
hws.assignin('sigma2', 0); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');
% signal émis : fréquence instantanée de fc - df à fc + df
s = so.get('sfm'); s = s(K); fi = diff(unwrap(angle(signal_analytique(s(:))))) * 200e3/(2*pi);
fi = conv(fi, ones(9,1)/9, 'same'); fi = fi(300:end-300);
ntot = ntot+1; nok = nok + verifier('FM emis : frequence instantanee max (Hz)', max(fi), 15e3, 100);
ntot = ntot+1; nok = nok + verifier('FM emis : frequence instantanee min (Hz)', min(fi), 5e3, 100);
y = so.get('yfm'); [~, a] = rsb_tonalite(y(K), 1e3, 200e3);
ntot = ntot+1; nok = nok + verifier('FM : amplitude restituee (Hz)', a, 5e3, 60);
hws.assignin('sigma2', 0.02); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');   % même modèle, canal bruité
y = so.get('yfm'); fprintf('     FM : RSB de sortie avec sigma2 = 0.02 : %.1f dB (reference : 33.1 dB)\n', rsb_tonalite(y(2001:10000), 1e3, 200e3));
if usejava('desktop'), open_system([mdl '/Scope']); end   % oscilloscope de la dernière simulation (canal bruité)
f = figure('Visible', 'off', 'Position', [0 0 900 600]); t = (0:numel(so.get('sfm'))-1)/200e3*1e3; k = t >= 5 & t <= 8;
s = so.get('sfm'); y = so.get('yfm'); subplot(2,1,1); plot(t(k), s(k)); title('mod\_fm : signal FM emis s(t)'); grid on;
subplot(2,1,2); plot(t(k), y(k)); title('Ecart de frequence demodule (Hz), sigma2 = 0,02'); xlabel('Temps (ms)'); grid on;
exportgraphics(f, fullfile(ici, 'mod_fm_resultat.png')); close(f);
save_system(mdl);

%% ===================== Modèle Simulink PM : modulateur de phase, canal et démodulateur par argument =====================
mdl = 'mod_pm';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
set_param(mdl, 'SolverType', 'Fixed-step', 'Solver', 'FixedStepDiscrete', 'FixedStep', '5e-06', 'StopTime', '0.05');
hws = get_param(mdl, 'ModelWorkspace');
fs = 200e3;
hws.assignin('fs', 200e3);
hws.assignin('fc', 10e3);
hws.assignin('fm', 1e3);
hws.assignin('bp', 1.5);
hws.assignin('phi', 0.7);
hws.assignin('sigma2', 0);
hws.assignin('hpre', lpf_hamming(8e3, fs, 201));
hws.assignin('hpost', lpf_hamming(4e3, fs, 201));
add_block('simulink/Sources/Sine Wave', [mdl '/Message'], 'Position', [280 40 340 90], 'Amplitude', 'bp', 'Frequency', '2*pi*fm', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Sources/Digital Clock', [mdl '/Horloge'], 'Position', [40 132 100 178], 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Gain', [mdl '/2 pi fc'], 'Position', [160 130 220 180], 'Gain', '2*pi*fc');
add_block('simulink/Sources/Constant', [mdl '/phi'], 'Position', [160 207 210 247], 'Value', 'phi');
add_block('simulink/Math Operations/Sum', [mdl '/Phase porteuse'], 'Position', [280 175 312 207], 'Inputs', '++');
add_block('simulink/Math Operations/Sum', [mdl '/Phase totale'], 'Position', [520 103 552 135], 'Inputs', '++');
add_block('simulink/Math Operations/Trigonometric Function', [mdl '/cos'], 'Position', [640 94 702 144], 'Operator', 'cos');
add_block('simulink/Sources/Random Number', [mdl '/Bruit'], 'Position', [640 184 700 234], 'Mean', '0', 'Variance', 'sigma2', 'Seed', '1', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Sum', [mdl '/Canal'], 'Position', [760 139 792 171], 'Inputs', '++');
add_block('simulink/Math Operations/Trigonometric Function', [mdl '/Porteuse non modulee'], 'Position', [520 247 582 297], 'Operator', 'cos');
add_block('simulink/Signal Routing/Mux', [mdl '/Mux PM'], 'Position', [880 201 890 271], 'Inputs', '2');
add_block('simulink/Sinks/To Workspace', [mdl '/spm'], 'Position', [880 46 965 84], 'VariableName', 'spm', 'SaveFormat', 'Array');
add_block('simulink/Sources/Sine Wave', [mdl '/OL cos'], 'Position', [40 328 100 378], 'Amplitude', '2', 'Frequency', '2*pi*fc', 'Phase', 'pi/2', 'SampleTime', '1/fs');
add_block('simulink/Sources/Sine Wave', [mdl '/OL -sin'], 'Position', [40 472 100 522], 'Amplitude', '-2', 'Frequency', '2*pi*fc', 'Phase', '0', 'SampleTime', '1/fs');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur I'], 'Position', [160 352 202 408], 'Inputs', '2');
add_block('simulink/Math Operations/Product', [mdl '/Melangeur Q'], 'Position', [160 442 202 498], 'Inputs', '2');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre I'], 'Position', [280 355 350 405], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre Q'], 'Position', [280 445 350 495], 'Numerator', 'hpre', 'Denominator', '1');
add_block('simulink/Math Operations/Real-Imag to Complex', [mdl '/Re-Im vers complexe'], 'Position', [400 368 460 428], 'Input', 'Real and imag');
add_block('simulink/Math Operations/Complex to Magnitude-Angle', [mdl '/arg'], 'Position', [520 373 580 423], 'Output', 'Angle');
add_block('simulink/Discrete/Discrete Filter', [mdl '/Filtre de sortie'], 'Position', [640 373 710 423], 'Numerator', 'hpost', 'Denominator', '1');
add_block('simulink/Sinks/To Workspace', [mdl '/ypm'], 'Position', [760 451 845 489], 'VariableName', 'ypm', 'SaveFormat', 'Array');
add_block('simulink/Sinks/Scope', [mdl '/Scope'], 'Position', [1000 154 1050 228], 'NumInputPorts', '3');
add_line(mdl, 'Horloge/1', '2 pi fc/1', 'autorouting', 'on');
add_line(mdl, '2 pi fc/1', 'Phase porteuse/1', 'autorouting', 'on');
add_line(mdl, 'phi/1', 'Phase porteuse/2', 'autorouting', 'on');
add_line(mdl, 'Message/1', 'Phase totale/1', 'autorouting', 'on');
add_line(mdl, 'Phase porteuse/1', 'Phase totale/2', 'autorouting', 'on');
add_line(mdl, 'Phase totale/1', 'cos/1', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'Canal/1', 'autorouting', 'on');
add_line(mdl, 'Bruit/1', 'Canal/2', 'autorouting', 'on');
add_line(mdl, 'Phase porteuse/1', 'Porteuse non modulee/1', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'Mux PM/1', 'autorouting', 'on');
add_line(mdl, 'Porteuse non modulee/1', 'Mux PM/2', 'autorouting', 'on');
add_line(mdl, 'cos/1', 'spm/1', 'autorouting', 'on');
add_line(mdl, 'OL cos/1', 'Melangeur I/1', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur I/2', 'autorouting', 'on');
add_line(mdl, 'Canal/1', 'Melangeur Q/1', 'autorouting', 'on');
add_line(mdl, 'OL -sin/1', 'Melangeur Q/2', 'autorouting', 'on');
add_line(mdl, 'Melangeur I/1', 'Filtre I/1', 'autorouting', 'on');
add_line(mdl, 'Melangeur Q/1', 'Filtre Q/1', 'autorouting', 'on');
add_line(mdl, 'Filtre I/1', 'Re-Im vers complexe/1', 'autorouting', 'on');
add_line(mdl, 'Filtre Q/1', 'Re-Im vers complexe/2', 'autorouting', 'on');
add_line(mdl, 'Re-Im vers complexe/1', 'arg/1', 'autorouting', 'on');
add_line(mdl, 'arg/1', 'Filtre de sortie/1', 'autorouting', 'on');
add_line(mdl, 'Filtre de sortie/1', 'ypm/1', 'autorouting', 'on');
add_line(mdl, 'Message/1', 'Scope/1', 'autorouting', 'on');
add_line(mdl, 'Mux PM/1', 'Scope/2', 'autorouting', 'on');
add_line(mdl, 'Filtre de sortie/1', 'Scope/3', 'autorouting', 'on');
save_system(mdl, fullfile(ici, [mdl '.slx']));
if usejava('desktop'), open_system(mdl); end
print(['-s' mdl], '-dpng', '-r150', fullfile(ici, [mdl '_schema.png']));   % schéma bloc exporté par Simulink
hws.assignin('sigma2', 0); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');
% signal émis : écart de phase avec la porteuse non modulée = kp.x(t)
s = so.get('spm'); t = (0:numel(s)-1).'/200e3; d = angle(signal_analytique(s(:)) .* exp(-1j*(2*pi*10e3*t + 0.7)));
[~, a] = rsb_tonalite(d(K), 1e3, 200e3);
ntot = ntot+1; nok = nok + verifier('PM emis : ecart de phase / porteuse (rad)', a, 1.5, 0.02);
y = so.get('ypm'); y = y(K) - mean(y(K)); [~, a] = rsb_tonalite(y, 1e3, 200e3);
ntot = ntot+1; nok = nok + verifier('PM : amplitude restituee (rad)', a, 1.5, 0.03);
hws.assignin('sigma2', 0.02); so = sim(mdl, 'ReturnWorkspaceOutputs', 'on');   % même modèle, canal bruité
y = so.get('ypm'); y = y(2001:10000) - mean(y(2001:10000));
fprintf('     PM : RSB de sortie avec sigma2 = 0.02 : %.1f dB (reference : 29.9 dB)\n', rsb_tonalite(y, 1e3, 200e3));
if usejava('desktop'), open_system([mdl '/Scope']); end   % oscilloscope de la dernière simulation (canal bruité)
f = figure('Visible', 'off', 'Position', [0 0 900 600]); t = (0:numel(so.get('spm'))-1)/200e3; k = t >= 5e-3 & t <= 8e-3;
s = so.get('spm'); y = so.get('ypm'); subplot(2,1,1); plot(t(k)*1e3, s(k), t(k)*1e3, cos(2*pi*10e3*t(k) + 0.7), '--'); title('mod\_pm : signal PM emis et porteuse non modulee'); grid on;
subplot(2,1,2); plot(t(k)*1e3, y(k)); title('Phase demodulee (rad), sigma2 = 0,02'); xlabel('Temps (ms)'); grid on;
exportgraphics(f, fullfile(ici, 'mod_pm_resultat.png')); close(f);
save_system(mdl);

fprintf('\nBilan Simulink : %d controles reussis sur %d\n', nok, ntot);
diary off;
if ~usejava('desktop') && nok < ntot, error('Des controles ont echoue'); end