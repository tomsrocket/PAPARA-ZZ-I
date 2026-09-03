function colorcode = fcn_color_id(colorId)
%% PAPARA(ZZ)I local extension: simple numbered color palette
% Enter only the number in a keyword list. MATLAB RGB values are kept here.
%
% 1 blue       2 orange      3 green       4 purple
% 5 turquoise  6 red         7 magenta     8 yellow
% 9 black     10 gray       11 white      12 dark blue

if nargin < 1 || isempty(colorId) || isnan(colorId) || colorId < 1
    colorId = 1;
end
colorId = round(colorId);

palette = [
    0.10 0.35 0.90; ... % 1 blue
    0.95 0.45 0.05; ... % 2 orange
    0.10 0.65 0.25; ... % 3 green
    0.55 0.20 0.80; ... % 4 purple
    0.00 0.65 0.65; ... % 5 turquoise
    0.90 0.10 0.10; ... % 6 red
    0.85 0.10 0.55; ... % 7 magenta
    0.95 0.75 0.05; ... % 8 yellow
    0.00 0.00 0.00; ... % 9 black
    0.50 0.50 0.50; ... % 10 gray
    1.00 1.00 1.00; ... % 11 white
    0.05 0.15 0.55  ... % 12 dark blue
    ];

if colorId > size(palette,1)
    colorId = mod(colorId-1,size(palette,1)) + 1;
end
colorcode = palette(colorId,:);
end
