function w = hann_(N)
%HANN_ Fenêtre de Hann (colonne), sans boîte à outils.
w = 0.5 - 0.5*cos(2*pi*(0:N-1).'/(N-1));
end
