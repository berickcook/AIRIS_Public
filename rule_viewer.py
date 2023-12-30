import numpy as np
import sys

knowledge = np.load('Knowledge.npy', allow_pickle=True).item()
sys.stdout = open('./rules_view.txt', 'w')
rule_count = 0
exception_count = 0
combine_count = 0
combined_count = 0
rule_val = None
rule_act = None

for val in knowledge['2d{']:
    if rule_val is not None and val != rule_val:
        continue
    else:
        print(print('\nNew Value ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'))
        for rule_id in knowledge['2d/' + str(val)]:
            cond_group = knowledge['2d/' + str(val) + '/' + str(rule_id)]
            if rule_id[:2:] == 'c-':
                combine_count += 1
            if rule_act is not None:
                try:
                    knowledge['2d/' + str(val) + '/' + str(cond_group) + '/act'][rule_act]
                except KeyError:
                    continue
            if knowledge['2d/' + str(val) + '/' + str(cond_group) + '/combined']:
                combined_count += 1
                continue
            print('Combined: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/combined'])
            rule_count += 1
            print('Value:', val)
            print('Rule:', rule_id)
            print('Condition Group:', cond_group)
            print('Action:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/act'])
            print('Change:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/abs'])
            print('Last Step:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lstep'])
            try:
                print('Last Rules: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/lrules'])
            except KeyError:
                print('Last Rules: NONE')
            try:
                group1d = knowledge['1d/0/' + str(rule_id)]
                print('Keys needed:', knowledge['1d/0/' + str(group1d) + '/oval'])
                print('Keys rel change:', knowledge['1d/0/' + str(group1d) + '/rel'])
                print('Keys abs change:', knowledge['1d/0/' + str(group1d) + '/abs'])

                group1d = knowledge['1d/1/' + str(rule_id)]
                print('Extinguishers needed:', knowledge['1d/1/' + str(group1d) + '/oval'])
                print('Extinguishers rel change:', knowledge['1d/1/' + str(group1d) + '/rel'])
                print('Extinguishers abs change:', knowledge['1d/1/' + str(group1d) + '/abs'])

                group1d = knowledge['1d/2/' + str(rule_id)]
                print('Batteries needed:', knowledge['1d/2/' + str(group1d) + '/oval'])
                print('Batteries rel change:', knowledge['1d/2/' + str(group1d) + '/rel'])
                print('Batteries abs change:', knowledge['1d/2/' + str(group1d) + '/abs'])
            except KeyError:
                pass
            print('Inclusions Relative:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/inclusions/rel'])
            try:
                print('Combined from:', knowledge['combined/' + rule_id])
            except KeyError:
                pass
            try:
                print('Exclusions: ', knowledge['exclusions/' + rule_id])
            except KeyError:
                pass
            try:
                print('Cleaned: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/inclusions/rel/cleaned'])
            except KeyError:
                pass
            try:
                print('Removed conditions: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/inclusions/rel/removed'])
            except KeyError:
                pass
            try:
                print('Mutual rules: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/mrules'])
            except KeyError:
                pass
            screen_input = []
            for x in range(20):
                screen_input.append([])
                for y in range(15):
                    screen_input[x].append(-999.0)

            origin_x = 10
            origin_y = 8

            if not knowledge['2d/' + str(val) + '/' + str(cond_group) + '/apos']:
                print('Absolute Position: NONE')
            else:
                for loc_key in knowledge['2d/' + str(val) + '/' + str(cond_group) + '/apos'].keys():
                    print('Absolute Position:', loc_key)
                    key = loc_key.split(':')
                    origin_x = int(key[0])
                    origin_y = int(key[1])

            if rule_id == 'c-67aa3c':
                origin_x = 4
                origin_y = 3

            screen_input[origin_x][origin_y] = val

            if not knowledge['2d/' + str(val) + '/' + str(cond_group) + '/inclusions/rel']:
                print('no change rule')
                print('\n--------------------------------------------------------------------------------------------------------------------------')
                continue

            for item in knowledge['2d/' + str(val) + '/' + str(cond_group) + '/inclusions/rel']:
                try:
                    if screen_input[origin_x + int(item[0])][origin_y + int(item[1])] == -999.0:
                        screen_input[origin_x + int(item[0])][origin_y + int(item[1])] = item[2]
                    else:
                        if screen_input[origin_x + int(item[0])][origin_y + int(item[1])] != item[2]:
                            screen_input[origin_x + int(item[0])][origin_y + int(item[1])] = 99.0
                except IndexError:
                    pass

            print('Prior conditions')
            t_format = np.array(screen_input).T

            for r, x in enumerate(t_format):
                x = ["%.0f" % i for i in x]
                for i, item in enumerate(x):
                    if item == '-999':
                        x[i] = '  '
                    elif int(item) < 10:
                        x[i] = ' ' + x[i]
                print(x, r)
            print('')
            print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")

            print('\nExceptions')
            try:
                for exception_id in knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions']:
                    exception_count += 1
                    screen_input = []
                    for x in range(20):
                        screen_input.append([])
                        for y in range(15):
                            screen_input[x].append(-999.0)

                    origin_x = 10
                    origin_y = 8

                    if not knowledge['2d/' + str(val) + '/' + str(cond_group) + '/apos']:
                        print('Absolute Position: NONE')
                    else:
                        for loc_key in knowledge['2d/' + str(val) + '/' + str(cond_group) + '/apos'].keys():
                            print('Absolute Position:', loc_key)
                            key = loc_key.split(':')
                            origin_x = int(key[0])
                            origin_y = int(key[1])

                    screen_input[origin_x][origin_y] = val

                    print('Exception:', exception_id)
                    print('Exception Action:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/act'])
                    print('Exception Last Step:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lstep'])
                    try:
                        print('Exception Last Rules:', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/lrules'])
                    except KeyError:
                        print('Exception Last Rules: NONE')

                    group1d = knowledge['1d/0/' + str(rule_id)]
                    print('Keys needed:', knowledge['1d/0/' + str(group1d) + '/exceptions/' + str(exception_id) + '/oval'])
                    print('Keys rel change:', knowledge['1d/0/' + str(group1d) + '/exceptions/' + str(exception_id) + '/rel'])

                    group1d = knowledge['1d/1/' + str(rule_id)]
                    print('Extinguishers needed:', knowledge['1d/1/' + str(group1d) + '/exceptions/' + str(exception_id) + '/oval'])
                    print('Extinguishers rel change:', knowledge['1d/1/' + str(group1d) + '/exceptions/' + str(exception_id) + '/rel'])

                    group1d = knowledge['1d/2/' + str(rule_id)]
                    print('Batteries needed:', knowledge['1d/2/' + str(group1d) + '/exceptions/' + str(exception_id) + '/oval'])
                    print('Batteries rel change:', knowledge['1d/2/' + str(group1d) + '/exceptions/' + str(exception_id) + '/rel'])

                    try:
                        print('Removed exception conditions: ', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/rel/removed'])
                    except KeyError:
                        pass

                    for item in knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/rel']:
                        try:
                            screen_input[origin_x + int(item[0])][origin_y + int(item[1])] = item[2]
                        except IndexError:
                            pass

                    print('Exception conditions', knowledge['2d/' + str(val) + '/' + str(cond_group) + '/exceptions/' + str(exception_id) + '/rel'])
                    t_format = np.array(screen_input).T

                    for r, x in enumerate(t_format):
                        x = ["%.0f" % i for i in x]
                        for i, item in enumerate(x):
                            if item == '-999':
                                x[i] = '  '
                            elif int(item) < 10:
                                x[i] = ' ' + x[i]
                        print(x, r)
                    print('')
                    print("[' 0', ' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']")
            except KeyError:
                print('No Exceptions')

            print('\n--------------------------------------------------------------------------------------------------------------------------')

print('Total number of rules:', rule_count)
print('Total number of exceptions:', exception_count)
print('Total of both:', rule_count + exception_count)
print('Total combined rules', combine_count)
print('Total rules combined', combined_count)

