import sys
import os
import constants
import logging
from sbs_general_matcher import log_handler
from PyQt4 import QtGui
from sbs_gui_main import SbSGuiMainController


LOGGER = logging.getLogger(__name__)


def main(lhc_mode=None, match_path=None, input_dir=None):
    sys.path.append(os.path.abspath("../../"))
    app = QtGui.QApplication(sys.argv)
    app.setStyle("plastique")
    main_controller = SbSGuiMainController()
    if match_path is None or lhc_mode is None:
        lhc_mode, match_path = main_controller.ask_for_initial_config(
            lhc_mode,
            match_path,
        )
        if match_path is None or lhc_mode is None:
            return
    log_handler.add_file_handler(LOGGER, match_path)
    if lhc_mode not in constants.LHC_MODES:
        raise ValueError("Invalid lhc mode, must be one of " +
                         str(constants.LHC_MODES))
    LOGGER.info("-------------------- ")
    LOGGER.info("Configuration:")
    LOGGER.info("- LHC mode: " + lhc_mode)
    LOGGER.info("- Match output path: " + os.path.abspath(match_path))
    LOGGER.info("-------------------- ")
    main_controller.set_match_path(match_path)
    main_controller.set_lhc_mode(lhc_mode)
    main_controller.set_input_dir(input_dir)
    main_controller.show_view()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
