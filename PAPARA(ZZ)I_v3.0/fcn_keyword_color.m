function colorcode = fcn_keyword_color(keyword,fig)
%% PAPARA(ZZ)I local extension: obtain the display color for a keyword
% The annotation text remains unchanged; this only controls visualization.

colorcode = fcn_color_id(1); % safe default: blue
if nargin < 2 || isempty(fig)
    fig = gcbf;
end
if isempty(fig) || ~ishandle(fig)
    return;
end

if ~isappdata(fig,'PAPARA_keyword_colors')
    return;
end

data = getappdata(fig,'PAPARA_keyword_colors');
if ~isstruct(data) || ~isfield(data,'keywords')
    return;
end

id = data.defaultColorId;
if isfield(data,'mode') && strcmpi(strtrim(data.mode),'individual')
    match = find(strcmp(data.keywords,keyword),1);
    if ~isempty(match) && isfield(data,'colorIds') && numel(data.colorIds) >= match
        id = data.colorIds(match);
    end
end
colorcode = fcn_color_id(id);
end
