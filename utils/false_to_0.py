def false_to_0(fname):
    """Changes all instances of \'false\' in a file to 0, and all instances of \'true\' to 1."""

    if fname == '':
        print('Error: Missing filename as argument.')
        return 0

    count = 0
    success = False
    with open(fname, 'r') as f:
        out_lines = []

        for line in f:
            line_spl = line.strip('\n').split(' ')
            for i, word in enumerate(line_spl):
                if word.lower() == 'false':
                    line_spl[i] = '0'
                    count = count + 1
                elif word.lower() == 'true':
                    line_spl[i] = '1'
                    count = count + 1

                if i == len(line_spl) - 1:
                    line_spl[i] = line_spl[i] + '\n'

            out_lines.append(' '.join(line_spl))

        success = True

    if success:
        with open(fname, 'w') as f_out:
            f_out.writelines(out_lines)

    return count

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Error: Missing filename as positional argument.')
    else:
        confirm = input(false_to_0.__doc__ + '\nAre you sure? (Y/n): ')
        if confirm == 'Y':
            print('Number of instances changed:', false_to_0(sys.argv[1]))
        else:
            print('Error: aborted.')
