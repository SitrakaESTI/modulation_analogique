function [rsb_db, amp] = rsb_tonalite(y, f, fs)
%RSB_TONALITE Rapport signal sur bruit d'une sortie censée contenir une
%   sinusoïde de fréquence f : ajustement par moindres carrés de
%   a*cos + b*sin + c, puis comparaison avec la puissance du résidu.
%   Le retard introduit par les filtres n'a aucune influence sur le résultat.
y = y(:); t = (0:numel(y)-1).'/fs;
A = [cos(2*pi*f*t), sin(2*pi*f*t), ones(size(t))];
c = A\y; res = y - A*c;
ps = (c(1)^2 + c(2)^2)/2;
rsb_db = 10*log10(ps/mean(res.^2));
amp = hypot(c(1), c(2));
end
