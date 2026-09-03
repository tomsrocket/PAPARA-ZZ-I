function strlist = fcn_keywords(hlist)
%% PAPARA(ZZ)I local extension: keyword lists with optional color IDs
% The original keyword-list behavior is preserved.
% Optional format:
%   #MODE=INDIVIDUAL
%   #DEFAULT=1
%   keyword<TAB>color_id
% If no color ID is given, the default color is used.

strlist = {};

[FileName,PathName,~] = uigetfile({'*.txt',...
    'Text file (*.txt)'; '*.*', 'All Files (*.*)'}, ...
    'Select the list of keywords');
if FileName==0, return; end
infile = fullfile(PathName,FileName);

mode = 'single';
defaultColorId = 1;
explicitColor = false;
colorIds = [];

fid = fopen(infile,'r');
if fid == -1
    errordlg('The selected keyword file could not be opened.','File error','modal');
    return;
end

while ~feof(fid)
    rawline = fgetl(fid);
    if ~ischar(rawline), continue; end
    line = strtrim(rawline);
    if isempty(line), continue; end

    % Header/comment lines
    if line(1) == '#'
        upperLine = upper(line);
        if strncmp(upperLine,'#MODE=',6)
            mode = strtrim(line(7:end));
        elseif strncmp(upperLine,'#DEFAULT=',9)
            tmp = str2double(strtrim(line(10:end)));
            if ~isnan(tmp) && tmp >= 1
                defaultColorId = round(tmp);
            end
        elseif strncmp(upperLine,'#COLOR=',7)
            tmp = str2double(strtrim(line(8:end)));
            if ~isnan(tmp) && tmp >= 1
                defaultColorId = round(tmp);
            end
        end
        continue;
    end

    % A tab separates the keyword from its optional color ID.
    tabpos = strfind(rawline,sprintf('\t'));
    if isempty(tabpos)
        keyword = strtrim(rawline);
        colorId = defaultColorId;
    else
        keyword = strtrim(rawline(1:tabpos(1)-1));
        colorId = str2double(strtrim(rawline(tabpos(1)+1:end)));
        if isempty(keyword)
            continue;
        end
        if isnan(colorId) || colorId < 1
            colorId = defaultColorId;
        else
            colorId = round(colorId);
            explicitColor = true;
        end
    end

    if isempty(keyword), continue; end
    strlist = [strlist; {keyword}]; %#ok<AGROW>
    colorIds = [colorIds; colorId]; %#ok<AGROW>
end
fclose(fid);

if isempty(strlist)
    strlist = {' '};
end

% If IDs were supplied but no mode header exists, use individual colors.
if explicitColor && ~strcmpi(strtrim(mode),'single')
    mode = 'individual';
elseif explicitColor && strcmpi(strtrim(mode),'single')
    mode = 'single';
end

% Store the color settings on the main figure for all callbacks and redraws.
fig = ancestor(hlist,'figure');
colorData = struct();
colorData.keywords = strlist;
colorData.colorIds = colorIds;
colorData.mode = strtrim(mode);
colorData.defaultColorId = defaultColorId;
colorData.sourceFile = infile;
setappdata(fig,'PAPARA_keyword_colors',colorData);

set(hlist,'Value',1);
set(hlist,'String',strlist);

end
