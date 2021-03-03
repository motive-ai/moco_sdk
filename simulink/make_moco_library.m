function make_moco_library
libname = 'moco_lib';
if any(strcmp(find_system('searchdepth',0),libname))
    close_system(libname, 0);
end
h = new_system(libname, 'Library');
open_system(h)

x = 0;
fill_blocks('moco_receive*.mexa64');
x = 150;
fill_blocks('moco_mode*.mexa64');
x = 300;
fill_blocks('moco_command*.mexa64');
x = 450;
fill_blocks('moco_init*.mexa64');
save_system(h)

    function fill_blocks(filename)
    mex_files = dir(filename);
    for i = 1:length(mex_files)
        width = 50;
        height = 50;

        y = 1.5*i*height;
        [~,name] = fileparts(mex_files(i).name);
        mh = add_block('built-in/S-Function',[libname, '/', name], 'Position', [x, y, x+width, y+height]);
        if strcmp(name,'moco_init')
            set_param(mh, 'FunctionName', name, 'parameters', '0');
        else
            set_param(mh, 'FunctionName', name);
        end
    end

    end
end

