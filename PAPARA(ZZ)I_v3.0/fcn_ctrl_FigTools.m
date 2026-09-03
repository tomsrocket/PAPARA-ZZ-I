function [hPoints,hSave] = fcn_ctrl_FigTools(h,onoff,cbPrevSection,...
    cbNextSection,cbMeas,cbRect,cbPoly,cbIgnore,cbPoints,cbSave,cbExport,cbHelp,...
    cbAbout)
%% Copyright 2015-2022 Yann Marcon and Autun Purser

% This file is part of PAPARA(ZZ)I.
% 
% PAPARA(ZZ)I is free software: you can redistribute it and/or modify
% it under the terms of the GNU General Public License as published by
% the Free Software Foundation, either version 3 of the License, or
% (at your option) any later version.
% 
% PAPARA(ZZ)I is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
% 
% You should have received a copy of the GNU General Public License
% along with PAPARA(ZZ)I.  If not, see <http://www.gnu.org/licenses/>.


%% Contact:
% Yann Marcon: ymarcon@marum.de
% Autun Purser: autun.purser@awi.de




%%
if exist('h','var')~=1, h = gcf; end
if exist('onoff','var')~=1 || ~strcmp(onoff,'on'), onoff = 'off'; end

hToolbar = findall(h,'Tag','FigureToolBar');

allh = []; % list of handles
allh = [ allh , findall(h,'Tag','Standard.NewFigure')];
allh = [ allh , findall(h,'Tag','Standard.FileOpen')];
allh = [ allh , findall(h,'Tag','Standard.SaveFigure')];
allh = [ allh , findall(h,'Tag','Standard.PrintFigure')];
allh = [ allh , findall(h,'Tag','Standard.EditPlot')];
allh = [ allh , findall(h,'Tag','Standard.OpenInspector')];
% allh = [ allh , findall(h,'Tag','Exploration.ZoomIn')];
% allh = [ allh , findall(h,'Tag','Exploration.ZoomOut')];
% allh = [ allh , findall(h,'Tag','Exploration.Pan')];
allh = [ allh , findall(h,'Tag','Exploration.Rotate')];
allh = [ allh , findall(h,'Tag','Exploration.DataCursor')];
allh = [ allh , findall(h,'Tag','Exploration.Brushing')];
allh = [ allh , findall(h,'Tag','DataManager.Linking')];
allh = [ allh , findall(h,'Tag','Annotation.InsertColorbar')];
allh = [ allh , findall(h,'Tag','Annotation.InsertLegend')];
allh = [ allh , findall(h,'Tag','Plottools.PlottoolsOff')];
allh = [ allh , findall(h,'Tag','Plottools.PlottoolsOn')];
set(allh,'Visible',onoff);

% Separators
set(findall(h,'Tag','Standard.EditPlot'),'Separator',onoff);
set(findall(h,'Tag','Exploration.ZoomIn'),'Separator',onoff);
set(findall(h,'Tag','DataManager.Linking'),'Separator',onoff);
set(findall(h,'Tag','Annotation.InsertColorbar'),'Separator',onoff);
set(findall(h,'Tag','Plottools.PlottoolsOff'),'Separator',onoff);



%% Previous button
cdata = fcn_icon('ico_arrow_left.gif',[255 255 255]);

% Add the icon to the latest toolbar
hPrev = uipushtool(hToolbar,'CData',cdata,'Tag','ChangeImageButtons',...
    'TooltipString','Previous image section', 'ClickedCallback',cbPrevSection);



%% Next button
cdata = fcn_icon('ico_arrow_right.gif',[255 255 255]);

% Add the icon to the latest toolbar
hNext = uipushtool(hToolbar,'CData',cdata,'Tag','ChangeImageButtons',...
    'TooltipString','Next image section', 'ClickedCallback',cbNextSection);



%% Measure button
cdata = fcn_icon('ico_measure.gif',[255 255 255]);

% Add the icon to the latest toolbar
hMeas = uitoggletool(hToolbar,'CData',cdata,'Tag','Toolbar_Measure',...
    'TooltipString','Measure selected feature', 'ClickedCallback',cbMeas);



%% Rectangle button
cdata = fcn_icon('ico_rectangle.gif',[255 255 255]);

% Add the icon to the latest toolbar
hRect = uitoggletool(hToolbar,'CData',cdata,'Tag','Toolbar_Rectangle',...
    'TooltipString','Select usable rectangle area', 'ClickedCallback',cbRect);



%% Polygon button
cdata = fcn_icon('ico_polygon.gif',[255 255 255]);

% Add the icon to the latest toolbar
hPoly = uitoggletool(hToolbar,'CData',cdata,'Tag','Toolbar_Polygon',...
    'TooltipString','Select usable polygon area', 'ClickedCallback',cbPoly);



%% Ignore button
cdata = fcn_icon('ico_ignore_image.gif',[255 255 255]);

% Add the icon to the latest toolbar
hIgnore = uitoggletool(hToolbar,'CData',cdata,'Tag','Toolbar_Ignore',...
    'TooltipString','Ignore image', 'ClickedCallback',cbIgnore);



%% Create point tool
% The old uitogglesplittool and Java dropdown menu were removed from
% current MATLAB versions. The point generator is not needed for manual
% annotations, so retain only a harmless toggle button.
cdata = fcn_icon('ico_points_random.gif',[255 0 255]);
hPoints = uitoggletool(hToolbar,'CData',cdata,'Tag','Toolbar_Points',...
    'TooltipString','Generated points (not used for manual annotations)',...
    'ClickedCallback',cbPoints{1});


%% Save screenshot buttons
% Use ordinary toolbar buttons so no Java/SplitToolbar dependency is needed.
cdata = fcn_icon('ico_image_screenshot.gif',[255 255 255]);
hSave = uipushtool(hToolbar,'CData',cdata,'Tag','Toolbar_ImageSavePNG', ...
    'TooltipString','Export current image as PNG', ...
    'ClickedCallback',cbSave{2});
hSaveJPG = uipushtool(hToolbar,'CData',cdata,'Tag','Toolbar_ImageSaveJPG', ...
    'TooltipString','Export current image as JPG', ...
    'ClickedCallback',cbSave{3});


%% Export button
cdata = fcn_icon('ico_export_results.gif',[255 255 255]);

% Add the icon to the latest toolbar
hExport = uipushtool(hToolbar,'CData',cdata,'Tag','ExportResults',...
    'TooltipString','Export results', 'ClickedCallback',cbExport);



%% Help button
cdata = fcn_icon('ico_help.gif',[255 255 255]);

% Add the icon to the latest toolbar
hHelp = uipushtool(hToolbar,'CData',cdata, 'TooltipString','Help','ClickedCallback',cbHelp);



%% About button
cdata = fcn_icon('ico_about.gif',[255 255 255]);

% Add the icon to the latest toolbar
hAbout = uipushtool(hToolbar,'CData',cdata, 'TooltipString','About PAPARA(ZZ)I','ClickedCallback',cbAbout);


%% Re-order buttons
% hButtons = allchild(hToolbar);
% hVisibleButtons = findobj(hButtons,'Visible','on');
% set(hToolbar,'Children',hButtons([1:6,17:19,7:8,9:16])); % for some reason, handles are ordered from right to left


%% Separators
set(hPrev,'Separator','on');
set(findall(h,'Tag','Exploration.ZoomIn'),'Separator','on');
set(hMeas,'Separator','on');
set(hSave,'Separator','on');
set(hSaveJPG,'Separator','off');
set(hHelp,'Separator','on');
set(hAbout,'Separator','on');


end