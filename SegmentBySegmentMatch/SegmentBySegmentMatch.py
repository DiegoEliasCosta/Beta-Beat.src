import __init__  # @UnusedImport used for appending paths
import os
import shutil
import optparse
from Utilities import iotools
import subprocess
from Python_Classes4MAD.metaclass import twiss
from Python_Classes4MAD import madxrunner
import json
import numpy as np
from SegmentBySegment import SegmentBySegment
import Utilities


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
ALL_LISTS_BEAM1_PATH = os.path.join(CURRENT_PATH, '..', 'MODEL', 'LHCB', 'fullresponse', 'LHCB1', 'AllLists.json')
ALL_LISTS_BEAM2_PATH = os.path.join(CURRENT_PATH, '..', 'MODEL', 'LHCB', 'fullresponse', 'LHCB2', 'AllLists.json')

_IP2_FIX_START = 214.0
_IP2_FIX_END = 841.0
_IP8_FIX_START = 511.0
_IP8_FIX_END = 26532.0


def parse_args():
    parser = optparse.OptionParser()
    parser.add_option("--ip",
                    help="Which interaction point: 1, 2, 3...",
                    metavar="IP", default="1", dest="ip")
    parser.add_option("--beam1",
                    help="Path to the measurement files for beam 1",
                    metavar="BEAM1", dest="b1")
    parser.add_option("--beam2",
                    help="Path to the measurement files for beam 2",
                    metavar="BEAM2", dest="b2")
    parser.add_option("-t", "--temp",
                    help="Path to the a temporary folder",
                    metavar="TEMP", default="", dest="temp")
    parser.add_option("--exclude",
                    help="Variables to exclude",
                    metavar="EXCLUDE", default="", dest="exclude")
    (options, args) = parser.parse_args()
    return options, args


def main(options, args):
    if len(args) > 0:
        command = args[0]
    else:
        command = "match"
    ip = options.ip
    temporary_path = options.temp
    match_temporary_path = os.path.join(temporary_path, "match")
    if command == "variables":
        exclude_vars_string = options.exclude
        generate_variables(ip, match_temporary_path, exclude_vars_string)
    elif command == "constraints":
        sbs_data_b1_path = options.b1
        sbs_data_b2_path = options.b2
        exclude_constr_string = options.exclude
        generate_constraints(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path, exclude_constr_string)
    elif command == "clean":
        clean_up_temporary_dir(match_temporary_path)
    else:
        sbs_data_b1_path = options.b1
        sbs_data_b2_path = options.b2
        temporary_path = options.temp
        match(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path)


def match(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path):

    beam1_temporary_path = os.path.join(match_temporary_path, "Beam1")
    beam2_temporary_path = os.path.join(match_temporary_path, "Beam2")

    iotools.create_dirs(os.path.join(beam1_temporary_path, "sbs"))
    iotools.create_dirs(os.path.join(beam2_temporary_path, "sbs"))

    _check_and_run_genvariables(ip, match_temporary_path)
    _check_and_run_genconstraints(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path)
    run_genphases(ip, match_temporary_path, sbs_data_b1_path, sbs_data_b2_path)

    print "Copying plotting files into temporary folder..."
    iotools.copy_item(os.path.join(CURRENT_PATH, "dumpB1.gplot"), match_temporary_path)
    iotools.copy_item(os.path.join(CURRENT_PATH, "dumpB2.gplot"), match_temporary_path)

    _copy_beam1_temp_files(ip, sbs_data_b1_path, beam1_temporary_path)

    _copy_beam2_temp_files(ip, sbs_data_b2_path, beam2_temporary_path)

    print "Getting matching range..."
    ((range_beam1_start_s, range_beam1_start_name),
    (range_beam1_end_s, range_beam1_end_name)) = _get_match_bpm_range(os.path.join(beam1_temporary_path, "sbs",
                                                                           "sbsphasext_IP" + ip + ".out"))
    ((range_beam2_start_s, range_beam2_start_name),
    (range_beam2_end_s, range_beam2_end_name)) = _get_match_bpm_range(os.path.join(beam2_temporary_path, "sbs",
                                                                           "sbsphasext_IP" + ip + ".out"))
    print "Matching range for Beam 1:", range_beam1_start_name, range_beam1_end_name
    print "Matching range for Beam 2:", range_beam2_start_name, range_beam2_end_name

    print "Running MADX..."
    label = "IP" + str(ip)
    _prepare_script_and_run_madx(label, beam1_temporary_path, beam2_temporary_path, match_temporary_path,
                                 range_beam1_start_name, range_beam1_end_name,
                                 range_beam2_start_name, range_beam2_end_name)

    print "Writting sbs files from MADX results..."
    _write_sbs_data(ip, beam1_temporary_path, beam2_temporary_path, range_beam1_start_name, range_beam2_start_name)

    print "Building changeparameters_match.madx..."
    _build_changeparameters_file(match_temporary_path)

    print "Running GNUPlot..."
    _prepare_and_run_gnuplot(ip, match_temporary_path,
                             range_beam1_start_s, range_beam1_end_s, range_beam2_start_s, range_beam2_end_s)

    print "Done"


def _check_and_run_genvariables(ip, match_temporary_path):
    for file_name in ["applycorrection.seqx", "dvariables.seqx", "genchangpars.seqx",
                      "svariables.seqx", "variablesb1.seqx", "variablesb2.seqx", "variablesc.seqx"]:
        full_file_path = os.path.join(match_temporary_path, file_name)
        if not os.path.exists(full_file_path):  # TODO: Here the variables should be recreated if they are for a different IP
            print "File " + file_name + " not found, generating new variables files..."
            generate_variables(ip, match_temporary_path)
            break


def _check_and_run_genconstraints(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path):
    for file_name in ["constraintsb1.seqx", "constraintsb2.seqx", "dumpb1.seqx", "dumpb2.seqx"]:
        full_file_path = os.path.join(match_temporary_path, file_name)
        if not os.path.exists(full_file_path):  # TODO: Here the constraints should be recreated if they are for a different IP
            print "File " + file_name + " not found, generating new constraints files..."
            generate_constraints(ip, sbs_data_b1_path, sbs_data_b2_path, match_temporary_path)
            break


def generate_variables(ip, variables_path=os.path.join(CURRENT_PATH, "match"), exclude_string=""):
    if not os.path.exists(variables_path):
        iotools.create_dirs(variables_path)

    exclude_list = _parse_exclude_string(exclude_string)

    variables_beam1 = json.load(file(ALL_LISTS_BEAM1_PATH, 'r'))['getListsByIR'][1]
    variables_common, variables_beam2 = json.load(file(ALL_LISTS_BEAM2_PATH, 'r'))['getListsByIR']

    ip_string = str(ip)

    apply_correction_file = open(os.path.join(variables_path, "applycorrection.seqx"), 'w')
    variables_common_file = open(os.path.join(variables_path, "variablesc.seqx"), 'w')
    variables_beam1_file = open(os.path.join(variables_path, "variablesb1.seqx"), 'w')
    variables_beam2_file = open(os.path.join(variables_path, "variablesb2.seqx"), 'w')
    variables_s_file = open(os.path.join(variables_path, "svariables.seqx"), 'w')
    variables_d_file = open(os.path.join(variables_path, "dvariables.seqx"), 'w')

    param_change_generator_file = open(os.path.join(variables_path, "genchangpars.seqx"), 'w')
    param_change_generator_file.write('select,flag=save, clear;')

    variables = variables_beam1[ip_string]
    param_change_generator_file.write('!B1\n')
    _vars_to_files(apply_correction_file, variables_beam1_file, variables_s_file,
                   variables_d_file, param_change_generator_file, variables, exclude_list)

    variables = variables_beam2[ip_string]
    param_change_generator_file.write('\n!B2\n')
    _vars_to_files(apply_correction_file, variables_beam2_file, variables_s_file,
                   variables_d_file, param_change_generator_file, variables, exclude_list)

    variables = variables_common[ip_string]
    param_change_generator_file.write('\n!B1 and B2\n')
    _vars_to_files(apply_correction_file, variables_common_file, variables_s_file,
                   variables_d_file, param_change_generator_file, variables, exclude_list)

    variables_common_file.close()
    variables_beam1_file.close()
    variables_beam2_file.close()
    variables_s_file.close()
    variables_d_file.close()

    param_change_generator_file.write('\n save, file=\"changeparameters.madx\";\n')
    param_change_generator_file.close()


def _vars_to_files(apply_correction_file, variables_file, variables_s_file, variables_d_file, param_change_generator_file, variables, excluded):
    for variable in variables:
        if variable not in excluded:
            variables_file.write('   vary, name=d' + variable + ', step:=1e-4;\n')
        variables_s_file.write(' ' + variable + '_0 = ' + variable + ';\n')
        variables_d_file.write(' ' + variable + ' := ' + variable + '_0 + d' + variable + ';\n')
        param_change_generator_file.write('select,flag=save,pattern=\"d' + variable + '\";\n')
        apply_correction_file.write(variable + ' = ' + variable + '_0 + d' + variable + ';\n')


def generate_constraints(ip, sbs_data_b1_path, sbs_data_b2_path, constraints_path=os.path.join(CURRENT_PATH, "match"), exclude_string=""):
    full_data_beam1 = twiss(os.path.join(sbs_data_b1_path, 'getphasex.out'))
    x_tune_beam1 = full_data_beam1.Q1
    y_tune_beam1 = full_data_beam1.Q2

    full_data_beam2 = twiss(os.path.join(sbs_data_b2_path, 'getphasex.out'))
    x_tune_beam2 = full_data_beam2.Q1
    y_tune_beam2 = full_data_beam2.Q2

    sbs_x_data_beam1 = twiss(os.path.join(sbs_data_b1_path, 'sbs', 'sbsphasext_IP' + ip + '.out'))
    sbs_y_data_beam1 = twiss(os.path.join(sbs_data_b1_path, 'sbs', 'sbsphaseyt_IP' + ip + '.out'))
    sbs_x_data_beam2 = twiss(os.path.join(sbs_data_b2_path, 'sbs', 'sbsphasext_IP' + ip + '.out'))
    sbs_y_data_beam2 = twiss(os.path.join(sbs_data_b2_path, 'sbs', 'sbsphaseyt_IP' + ip + '.out'))

    constr_file_beam1 = open(os.path.join(constraints_path, 'constraintsb1.seqx'), 'w')
    constr_file_beam2 = open(os.path.join(constraints_path, 'constraintsb2.seqx'), 'w')
    dump_file_beam1 = open(os.path.join(constraints_path, "dumpb1.seqx"), 'w')
    dump_file_beam2 = open(os.path.join(constraints_path, "dumpb2.seqx"), 'w')

    if exclude_string.strip() == "":
        exclude_list_x = ""
        exclude_list_y = ""
    else:
        exclude_both_planes = exclude_string.split(";")
        exclude_list_x = _parse_exclude_string(exclude_both_planes[0])
        exclude_list_y = _parse_exclude_string(exclude_both_planes[1])

    _write_constraints_file(sbs_x_data_beam1, constr_file_beam1, dump_file_beam1, ip, 1, "x", x_tune_beam1, exclude_list_x)
    _write_constraints_file(sbs_y_data_beam1, constr_file_beam1, dump_file_beam1, ip, 1, "y", y_tune_beam1, exclude_list_y)
    _write_constraints_file(sbs_x_data_beam2, constr_file_beam2, dump_file_beam2, ip, 2, "x", x_tune_beam2, exclude_list_x)
    _write_constraints_file(sbs_y_data_beam2, constr_file_beam2, dump_file_beam2, ip, 2, "y", y_tune_beam2, exclude_list_y)


def _write_constraints_file(sbs_data, constr_file, dump_file, ip, beam, plane, tune, exclude_list):
    if plane == "x":
        constr_file.write('\n!!!! BEAM ' + str(beam) + ' H !!!!!\n\n')
    else:
        constr_file.write('\n!!!! BEAM ' + str(beam) + ' V !!!!!\n\n')

    dump_file.write('delete,table=dmu' + plane + 'b' + str(beam) + ';\n')
    dump_file.write('create,table=dmu' + plane + 'b' + str(beam) +
                    ',column=sss,cdmu' + plane +
                    ',tdmu' + plane + ';\n')

    for index in range(0, len(sbs_data.NAME)):
        name = sbs_data.NAME[index]
        if name not in exclude_list:
            phase = sbs_data.PROPPHASEX[index] if plane == "x" else sbs_data.PROPPHASEY[index]
            s = sbs_data.S[index]

            phase, ckstr = _check_and_fix_tune_discontinuity(phase, s, ip, beam, plane, tune)

            weight = 1e-6 if abs(phase) > 0.25 else 1

            constr_file.write('   constraint, weight = ' + str(weight) + ' , ')
            constr_file.write('expr =  dmu' + plane + name + ' = ' + str(phase) + '; ')

            constr_file.write('!   S = ' + str(s) + ' ' + ckstr)
            constr_file.write(';\n')

            dump_file.write('   sss = table(twiss, ' + name + ', s); cdmu' +
                            plane + ' = dmu' + plane + name + ';  tdmu' + plane + ' =  ' + str(phase) + ';\n')
            dump_file.write('   fill,table=dmu' + plane + 'b' + str(beam) + ';\n')

    dump_file.write('write,table=dmu' + plane + 'b' + str(beam) + ', file=dmu' + plane + 'b' + str(beam) + '.tfs;\n')


def _check_and_fix_tune_discontinuity(phase, s, ip, beam, plane, tune):
    if ip == "2" and beam == 1 and s > _IP2_FIX_START and s < _IP2_FIX_END:
        return phase + tune, '+ B1 Q' + plane + '(' + str(tune) + ')'
    elif ip == "8" and beam == 2 and (s < _IP8_FIX_START or s > _IP8_FIX_END):
        return phase + tune, '+ B2 Q' + plane + '(' + str(tune) + ')'
    else:
        return phase, '+ 0.0'


def _parse_exclude_string(exclude_string):
    if not exclude_string == "":
        exclude_list = [var_name.strip() for var_name in exclude_string.strip('"').split(",")]
    else:
        exclude_list = []
    return exclude_list


def run_genphases(ip, match_temporary_path, sbs_data_b1_path, sbs_data_b2_path):

    sbs_x_data_beam1 = twiss(os.path.join(sbs_data_b1_path, 'sbs', 'sbsphasext_IP' + ip + '.out'))
    sbs_y_data_beam1 = twiss(os.path.join(sbs_data_b1_path, 'sbs', 'sbsphaseyt_IP' + ip + '.out'))
    sbs_x_data_beam2 = twiss(os.path.join(sbs_data_b2_path, 'sbs', 'sbsphasext_IP' + ip + '.out'))
    sbs_y_data_beam2 = twiss(os.path.join(sbs_data_b2_path, 'sbs', 'sbsphaseyt_IP' + ip + '.out'))

    phases_file = open(os.path.join(match_temporary_path, "phases.seqx"), 'w')
    phases0_beam1_file = open(os.path.join(match_temporary_path, "phases0b1.seqx"), 'w')
    phases0_beam2_file = open(os.path.join(match_temporary_path, "phases0b2.seqx"), 'w')

    beam1_s_list = sbs_x_data_beam1.MODEL_S
    sorted_index_beam1 = np.argsort(beam1_s_list)

    beam2_s_list = sbs_x_data_beam2.MODEL_S
    sorted_index_beam2 = np.argsort(beam2_s_list)

    phases_file.write('\n!!!! BEAM 1 H !!!!!\n\n')
    phases0_beam1_file.write('\n!!!! BEAM 1 H !!!!!\n\n')

    for name in sbs_x_data_beam1.NAME:
        phases0_beam1_file.write('mux0' + name + ' = ')
        phases0_beam1_file.write('table(twiss, ' + name + ', mux) - ')
        phases0_beam1_file.write('table(twiss, ' + sbs_x_data_beam1.NAME[sorted_index_beam1[0]] + ', mux);\n')

        phases_file.write('mux' + name + ' := ')
        phases_file.write('table(twiss, ' + name + ', mux) - ')
        phases_file.write('table(twiss, ' + sbs_x_data_beam1.NAME[sorted_index_beam1[0]] + ', mux);\n')

    phases_file.write('\n')

    for name in sbs_x_data_beam1.NAME:
        phases_file.write('dmux' + name + ' := ')
        phases_file.write('mux' + name + ' - ' 'mux0' + name + ';\n')

    phases_file.write('\n!!!! BEAM 2 H !!!!!\n\n')

    phases0_beam2_file.write('\n!!!! BEAM 2 H !!!!!\n\n')

    for idx in sorted_index_beam2:
        name = sbs_x_data_beam2.NAME[idx]

        phases0_beam2_file.write('mux0' + name + ' = ')
        phases0_beam2_file.write('table(twiss, ' + name + ', mux) - ')
        phases0_beam2_file.write('table(twiss, ' + sbs_x_data_beam2.NAME[sorted_index_beam2[0]] + ', mux);\n')

        phases_file.write('mux' + name + ' := ')
        phases_file.write('table(twiss, ' + name + ', mux) - ')
        phases_file.write('table(twiss, ' + sbs_x_data_beam2.NAME[sorted_index_beam2[0]] + ', mux);\n')

    phases_file.write('\n')

    for name in sbs_x_data_beam2.NAME:
        phases_file.write('dmux' + name + ' := ')
        phases_file.write('mux' + name + ' - ' 'mux0' + name + ';\n')

    beam1_s_list = sbs_y_data_beam1.MODEL_S
    sorted_index_beam1 = np.argsort(beam1_s_list)

    beam2_s_list = sbs_y_data_beam2.MODEL_S
    sorted_index_beam2 = np.argsort(beam2_s_list)

    phases_file.write('\n!!!! BEAM 1 V !!!!!\n\n')

    phases0_beam1_file.write('\n!!!! BEAM 1 V !!!!!\n\n')

    for name in sbs_y_data_beam1.NAME:

        phases0_beam1_file.write('muy0' + name + ' = ')
        phases0_beam1_file.write('table(twiss, ' + name + ', muy) - ')
        phases0_beam1_file.write('table(twiss, ' + sbs_y_data_beam1.NAME[sorted_index_beam1[0]] + ', muy);\n')

        phases_file.write('muy' + name + ' := ')
        phases_file.write('table(twiss, ' + name + ', muy) - ')
        phases_file.write('table(twiss, ' + sbs_y_data_beam1.NAME[sorted_index_beam1[0]] + ', muy);\n')

    phases_file.write('\n')

    for name in sbs_y_data_beam1.NAME:
        phases_file.write('dmuy' + name + ' := ')
        phases_file.write('muy' + name + ' - ' 'muy0' + name + ';\n')

    phases_file.write('\n!!!! BEAM 2 V !!!!!\n\n')

    phases0_beam2_file.write('\n!!!! BEAM 2 V !!!!!\n\n')

    for name in sbs_y_data_beam2.NAME:
        phases0_beam2_file.write('muy0' + name + ' = ')
        phases0_beam2_file.write('table(twiss, ' + name + ', muy) - ')
        phases0_beam2_file.write('table(twiss, ' + sbs_y_data_beam2.NAME[sorted_index_beam2[0]] + ', muy);\n')

        phases_file.write('muy' + name + ' := ')
        phases_file.write('table(twiss, ' + name + ', muy) - ')
        phases_file.write('table(twiss, ' + sbs_y_data_beam2.NAME[sorted_index_beam2[0]] + ', muy);\n')

    phases_file.write('\n')

    for name in sbs_y_data_beam2.NAME:
        phases_file.write('dmuy' + name + ' := ')
        phases_file.write('muy' + name + ' - ' 'muy0' + name + ';\n')

    phases0_beam1_file.close()
    phases0_beam2_file.close()
    phases_file.close()


def _copy_beam1_temp_files(ip, sbs_data_b1_path, beam1_temporary_path):
    _copy_files_with_extension(sbs_data_b1_path, beam1_temporary_path, ".out")
    _copy_files_with_extension(os.path.join(sbs_data_b1_path, "sbs"),
                               os.path.join(beam1_temporary_path, "sbs"),
                               ".madx")
    _copy_files_which_contains(os.path.join(sbs_data_b1_path, "sbs"),
                               os.path.join(beam1_temporary_path, "sbs"),
                               "IP" + str(ip))
    _copy_files_with_extension(os.path.join(sbs_data_b1_path, "sbs"),
                               os.path.join(beam1_temporary_path, "sbs"),
                               ".py")


def _apply_replace_to_beam1_files(sbs_data_b1_path, beam1_temporary_path, beam1_temporary_sbs_path, ip):
    strings_to_replace_madx = [("//", "/"),
                               (sbs_data_b1_path, beam1_temporary_path + "/"),
                               ("stop;", "return;"),
                               ("install,", "!install,")]
    strings_to_replace_ip = [("!!! Back propagation", "return;")]
    _replace_in_files_with_extension(beam1_temporary_sbs_path, strings_to_replace_madx, ".madx")
    _replace_in_files_with_extension(beam1_temporary_sbs_path, strings_to_replace_ip, "t_IP" + ip + ".madx")


def _copy_beam2_temp_files(ip, sbs_data_b2_path, beam2_temporary_path):
    _copy_files_with_extension(os.path.join(sbs_data_b2_path), beam2_temporary_path, ".out")
    _copy_files_with_extension(os.path.join(sbs_data_b2_path, "sbs"),
                               os.path.join(beam2_temporary_path, "sbs"),
                               ".madx")
    _copy_files_which_contains(os.path.join(sbs_data_b2_path, "sbs"),
                               os.path.join(beam2_temporary_path, "sbs"), "IP" + str(ip))
    _copy_files_with_extension(os.path.join(sbs_data_b2_path, "sbs"),
                               os.path.join(beam2_temporary_path, "sbs"),
                               ".py")


def _apply_replace_to_beam2_files(sbs_data_b2_path, beam2_temporary_path, beam2_temporary_sbs_path, ip):
    strings_to_replace_madx = [("//", "/"),
                               (sbs_data_b2_path, beam2_temporary_path + "/"),
                               ("stop;", "return;"),
                               ("install,", "!install,"),
                               ("label=b0", "label=b02"),
                               ("beta0=b0", "beta0=b02"),
                               ("label=b1", "label=b2"),
                               ("beta0=b1", "beta0=b2")]
    strings_to_replace_ip = [("!!! Back propagation", "return;")]
    strings_to_replace_madx_slash = [(".*back propagation.*", ("return;")), (".*\.seq.*", ("!!! No load seq")), (".*modifiers\.madx.*", ("!!! No load seq")), (".*install_additional_elements\.madx.*", ("!!! No load seq"))]
    _replace_in_files_with_extension(beam2_temporary_sbs_path, strings_to_replace_madx, ".madx")
    _replace_in_files_with_extension(beam2_temporary_sbs_path, strings_to_replace_ip, "t_IP" + ip + ".madx")
    _replace_in_files_with_extension(beam2_temporary_sbs_path, strings_to_replace_madx_slash, "t_IP" + ip + ".madx", "/")


def _get_match_bpm_range(file_path):
    twiss_data = twiss(file_path)
    bpms_with_distances_list = zip(twiss_data.MODEL_S, twiss_data.NAME)
    bpms_with_distances_list.sort()
    return bpms_with_distances_list[0], bpms_with_distances_list[-1]


def _prepare_script_and_run_madx(label, beam1_temporary_path, beam2_temporary_path, match_temporary_path,
                                 b1_range_start, b1_range_end, b2_range_start, b2_range_end):
    sbs_path = os.path.join(CURRENT_PATH, "..", "SegmentBySegment")
    dict_for_replacing = dict(
        PATHB1=os.path.join(beam1_temporary_path, "sbs"),
        PATHB2=os.path.join(beam2_temporary_path, "sbs"),
        MATCH=match_temporary_path,
        LABEL=label,
        SBSPATH=sbs_path,
        STARTFROMB1=b1_range_start,
        ENDATB1=b1_range_end,
        STARTFROMB2=b2_range_start,
        ENDATB2=b2_range_end
        )

    mask_file = os.path.join(CURRENT_PATH, "job.match.madx")
    madx_script_path = os.path.join(match_temporary_path, "job.match" + label + ".madx")

    Utilities.iotools.replace_keywords_in_textfile(mask_file, dict_for_replacing, madx_script_path)

    madxrunner.runForInputFile(madx_script_path, stdout=open(os.path.join(match_temporary_path, "match_madx_out.log"), "w"))


def _write_sbs_data(ip, beam1_temporary_path, beam2_temporary_path, range_beam1_start_name, range_beam2_start_name):
    save_path_b1 = os.path.join(beam1_temporary_path, "sbs")
    save_path_b2 = os.path.join(beam2_temporary_path, "sbs")
    input_data_b1 = SegmentBySegment._InputData(beam1_temporary_path)
    input_data_b2 = SegmentBySegment._InputData(beam2_temporary_path)
    prop_models_b1 = SegmentBySegment._PropagatedModels(save_path_b1, "IP" + str(ip))
    prop_models_b2 = SegmentBySegment._PropagatedModels(save_path_b2, "IP" + str(ip))

    SegmentBySegment.getAndWriteData("IP" + ip, input_data_b1, [], None, prop_models_b1, save_path_b1, False, False, "LHCB1", None)
    SegmentBySegment.getAndWriteData("IP" + ip, input_data_b2, [], None, prop_models_b2, save_path_b2, False, False, "LHCB2", None)


def _prepare_and_run_gnuplot(ip, match_temporary_path, range_beam1_start_s, range_beam1_end_s, range_beam2_start_s, range_beam2_end_s):
    beam1_plot_path = os.path.join(match_temporary_path, "IP" + ip + "B1.gplot")
    beam2_plot_path = os.path.join(match_temporary_path, "IP" + ip + "B2.gplot")
    beam1_plot_replacements = [("__IPNO__", str(ip)), ("__BEAMNO__", "1"),
        ("__FILENAME__", "IP" + str(ip) + "B1.eps"),
        ("__srangestart__", str(range_beam1_start_s)),
        ("__srangeend__", str(range_beam1_end_s))]
    beam2_plot_replacements = [("__IPNO__", str(ip)),
        ("__BEAMNO__", "2"),
        ("__FILENAME__", "IP" + str(ip) + "B2.eps"),
        ("__srangestart__", str(range_beam2_start_s)),
        ("__srangeend__", str(range_beam2_end_s))]
    iotools.copy_item(os.path.join(CURRENT_PATH, "templ.gplot"), beam1_plot_path)
    iotools.copy_item(os.path.join(CURRENT_PATH, "templ.gplot"), beam2_plot_path)
    if str(ip) == "2":
        iotools.copy_item(os.path.join(CURRENT_PATH, "templIP2B1.gplot"), beam1_plot_path)
        beam1_qx, beam1_qy = _get_q_value(match_temporary_path, 1)
        beam1_plot_replacements.append(("__QX__", beam1_qx))
        beam1_plot_replacements.append(("__QY__", beam1_qy))
    elif str(ip) == "8":
        iotools.copy_item(os.path.join(CURRENT_PATH, "templIP8B2.gplot"), beam2_plot_path)
        beam2_qx, beam2_qy = _get_q_value(match_temporary_path, 2)
        beam2_plot_replacements.append(("__QX__", beam2_qx))
        beam2_plot_replacements.append(("__QY__", beam2_qy))
    _replace_in_file(beam1_plot_path, beam1_plot_replacements)
    _replace_in_file(beam2_plot_path, beam2_plot_replacements)
    proccess_beam1 = subprocess.Popen("gnuplot " + beam1_plot_path, shell=True, cwd=match_temporary_path)
    proccess_beam2 = subprocess.Popen("gnuplot " + beam2_plot_path, shell=True, cwd=match_temporary_path)
    proccess_beam1.communicate()
    proccess_beam2.communicate()


def _get_q_value(match_temporary_path, beam_num):
    with open(os.path.join(match_temporary_path, "Beam" + str(beam_num), "getphasex.out")) as file_content:
        for line in file_content:
            line_pieces = line.split(" ")
            if line_pieces[1] == "Q1":
                qx = line_pieces[3].strip()
            elif line_pieces[1] == "Q2":
                qy = line_pieces[3].strip()
    return qx, qy


def clean_up_temporary_dir(match_temporary_path):
    os.unlink(os.path.join(match_temporary_path, "ats"))
    os.unlink(os.path.join(match_temporary_path, "db"))
    os.unlink(os.path.join(match_temporary_path, "db5"))
    os.unlink(os.path.join(match_temporary_path, "ds"))
    os.unlink(os.path.join(match_temporary_path, "lt"))
    iotools.delete_content_of_dir(match_temporary_path)


def _build_changeparameters_file(match_temporary_path):
    original_changeparameters_file = open(os.path.join(match_temporary_path, "changeparameters.madx"), "r")
    changeparameters_match_file = open(os.path.join(match_temporary_path, "changeparameters_match.madx"), "w")
    for original_line in original_changeparameters_file.readlines():
        parts = original_line.split("=")
        variable_name = parts[0].replace("d", "", 1).strip()
        variable_value = float(parts[1].replace(";", "").strip())
        print >> changeparameters_match_file, variable_name, " = ", variable_value, " + ", variable_name, ";"
    print >> changeparameters_match_file, "return;"


def _copy_files_with_extension(src, dest, ext):
    _copy_files_with_filter(src, dest, lambda file_name: file_name.endswith(ext))


def _copy_files_which_contains(src, dest, substring):
    _copy_files_with_filter(src, dest, lambda file_name: substring in file_name)


def _copy_files_with_filter(src, dest, filter_function):
    src_files = _get_filtered_file_list(src, filter_function)
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        shutil.copy(full_file_name, dest)


def _replace_in_files_with_extension(src, replace_pairs, ext, sed_sep="#"):
    src_files = _get_filtered_file_list(src, lambda file_name: file_name.endswith(ext))
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        _replace_in_file(full_file_name, replace_pairs, sed_sep)


def _replace_in_file(full_file_name, replace_pairs, sed_sep="#"):  # TODO: Use a python function instead of sed
    sed_command = "sed -i "
    for pattern, replace in replace_pairs:
        full_command = sed_command + "'s" + sed_sep + pattern + sed_sep + replace + sed_sep + "g' " + full_file_name
        subprocess.call(full_command, shell=True)


def _get_filtered_file_list(src, filter_function):
    filtered_file_list = []
    original_file_list = os.listdir(src)
    for file_name in original_file_list:
        if os.path.isfile(os.path.join(src, file_name)) and filter_function(file_name):
            filtered_file_list.append(file_name)
    return filtered_file_list


if __name__ == "__main__":
    (options, args) = parse_args()
    main(options, args)
