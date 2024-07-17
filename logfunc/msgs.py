from .config import MSG_FORMATS


def exit_msg(single_msg, func_name, exec_time, args_str, result_str, func_id):
    """builds the exit message for logf call"""

    if func_id is None:
        idname = '{}'.format(func_name)
    else:
        idname = '{} {}'.format(func_id, func_name)
    if single_msg:
        return MSG_FORMATS.single.format(
            func_name=func_name,
            exec_time=exec_time,
            args_str=args_str,
            result=result_str,
        )
    elif result_str:
        return MSG_FORMATS.exit.format(
            id_func_name=idname,
            exec_time=exec_time,
            args_str=args_str,
            result=result_str,
        )
    return MSG_FORMATS.exit_no_return.format(
        id_func_name=idname, exec_time=exec_time
    )
