%% LANCER_TOUT  Exécute les trois simulations MATLAB puis construit et
% vérifie les modèles Simulink si Simulink est installé.
% Chaque script commence par « clear » : le chemin est donc recalculé avant
% chaque appel.
run(fullfile(fileparts(mfilename('fullpath')), 'sim01_am_dbl_blu.m'));
run(fullfile(fileparts(mfilename('fullpath')), 'sim02_fm_pm.m'));
run(fullfile(fileparts(mfilename('fullpath')), 'sim04_interpolation.m'));
if ~isempty(ver('simulink'))
    run(fullfile(fileparts(mfilename('fullpath')), '..', 'Simulink', 'construire_et_verifier_modeles.m'));
end
