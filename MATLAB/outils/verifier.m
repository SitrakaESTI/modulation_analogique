function ok = verifier(nom, valeur, attendu, tolerance)
%VERIFIER Affiche une ligne de contrôle « OK » ou « ECHEC ».
ok = abs(valeur - attendu) <= tolerance;
if ok, etat = 'OK   '; else, etat = 'ECHEC'; end
fprintf('%s %s : %.3f (attendu %.3f +/- %g)\n', etat, nom, valeur, attendu, tolerance);
end
