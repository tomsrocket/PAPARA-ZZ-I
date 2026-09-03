function fcn_save_image(n,imagelist,inpath,userid,sep,h,imformat,annotype,pointtype,pointmax)
%% PAPARA(ZZ)I local extension: export the displayed image with annotations
% The image is captured from the axes, so visible annotation colours and
% open-circle markers are included in the exported PNG/JPG file.

if nargin < 7 || isempty(imformat)
    imformat = 'PNG';
end
if nargin < 8 || isempty(annotype)
    annotype = 'Annotation';
end

% Make sure the latest graphics state is rendered before capturing it.
drawnow;

% Image name and output folder
[~,iname,~] = fileparts([inpath imagelist{n}]);
imoutpath = [inpath userid '_exported_images' sep];
switch annotype
    case 'Annotation'
        imoutpath = [imoutpath 'free_annotations' sep];
    case 'GeneratedPoint'
        if nargin < 9 || isempty(pointtype), pointtype = 'grid'; end
        if nargin < 10 || isempty(pointmax), pointmax = 10; end
        imoutpath = sprintf('%s%s_%lipoints%s',imoutpath,pointtype,pointmax,sep);
end
if isdir(imoutpath) == 0
    mkdir(imoutpath);
end

% Capture the axes, including the image and all visible plot overlays.
% exportgraphics is preferred on current MATLAB versions. The getframe
% fallback also works on older versions.
fmt = upper(strtrim(imformat));
switch fmt
    case 'PNG'
        extension = '.png';
    case {'JPG','JPEG'}
        fmt = 'JPG';
        extension = '.jpg';
    otherwise
        error('PAPARA:UnsupportedImageFormat', ...
            'Only PNG and JPG export are supported by this test version.');
end
outfile = [imoutpath iname extension];

try
    if exist('exportgraphics','file') == 2
        exportgraphics(h,outfile,'Resolution',150);
    else
        frame = getframe(h);
        imageData = frame.cdata;
        if strcmp(fmt,'JPG')
            if ~isa(imageData,'uint8')
                imageData = im2uint8(imageData);
            end
            imwrite(imageData,outfile,'jpg','Quality',95);
        else
            imwrite(imageData,outfile,'png');
        end
    end
catch exportError
    % A second fallback is useful for graphics configurations where
    % exportgraphics cannot capture a hidden or embedded axes.
    try
        frame = getframe(h);
        imageData = frame.cdata;
        if strcmp(fmt,'JPG')
            if ~isa(imageData,'uint8')
                imageData = im2uint8(imageData);
            end
            imwrite(imageData,outfile,'jpg','Quality',95);
        else
            imwrite(imageData,outfile,'png');
        end
    catch captureError
        error('PAPARA:ImageExportFailed', ...
            'Image export failed: %s\nFallback failed: %s', ...
            exportError.message,captureError.message);
    end
end

msgbox(sprintf('Image exported to:\n%s',outfile), ...
    'Export finished','modal');
end
