# -*- coding: UTF-8 -*-
# This file is part of the jetson_stats package (https://github.com/rbonghi/jetson_stats or http://rnext.it).
# Copyright (c) 2019 Raffaello Bonghi.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from os import path
import operator
import curses
# Page class definition
from .jtopgui import Page
# Graphics elements
from .jtopguilib import (linear_gauge,
                         label_freq,
                         box_status)
# Graphics elements
from .jtopguilib import (box_keyboard,
                         size_min)
from .chart import Chart


class MEM(Page):

    def __init__(self, stdscr, jetson, refresh):
        super(MEM, self).__init__("MEM", stdscr, jetson, refresh)
        # Initialize MEM chart
        self.chart_ram = Chart(jetson, "RAM", refresh, self.update_chart, type_value=float, color=curses.color_pair(6), color_chart=curses.color_pair(12))

    def update_chart(self, jetson, name):
        parameter = jetson.stats.get("RAM", {})
        # Get max value if is present
        max_val = parameter.get("tot", 100)
        # Get unit
        unit = parameter.get("unit", "M")
        # Get value
        value = parameter.get("use", 0)
        info = size_min(max_val, start=unit)
        # Append in list
        return {
            'value': value / info[1],
            'max': info[0],
            'unit': info[2]
        }

    def swap_menu(self, lc, size, start, width):
        line_counter = lc + 1
        # SWAP linear gauge info
        swap_status = self.jetson.stats.get('SWAP', {})
        swap_cached = swap_status.get('cached', {})
        szw, divider, unit = size_min(swap_status['tot'], start=swap_status['unit'])
        percent = "{use}{unit}B/{tot}{unit}B".format(use=swap_status.get('use', 0) / divider,
                                                     tot=szw,
                                                     unit=unit)
        # Make label cache
        label = "(cached {size}{unit}B)".format(size=swap_cached.get('size', '0'), unit=swap_cached.get('unit', ''))
        self.stdscr.addstr(line_counter, start, "Swap", curses.A_BOLD)
        self.stdscr.addstr(line_counter, width - len(label) - 1, label, curses.A_NORMAL)
        # Add all swaps
        for swap in self.jetson.swap.swaps():
            line_counter += 1
            value = int(swap['used'] / float(swap['size']) * 100.0)
            # Extract size swap and unit
            szw, divider, unit = size_min(swap['size'])
            used = swap['used'] / divider
            # Change color for type partition
            if swap['type'] == 'partition':
                color = curses.color_pair(5)
            elif swap['type'] == 'file':
                color = curses.color_pair(3)
            else:
                color = curses.color_pair(6)
            linear_gauge(self.stdscr, offset=line_counter, size=size, start=start,
                         name=path.basename(swap['name']),
                         value=value,
                         percent="{use}/{tot}{unit}b".format(use=int(round(used)), tot=round(szw, 1), unit=unit),
                         label="P={prio: d}".format(prio=int(swap['prio'])),
                         color=color)
        # Draw total swap gauge
        line_counter += 1
        #self.stdscr.addstr(line_counter, start, "-" * (size - 1), curses.A_NORMAL)
        self.stdscr.hline(line_counter, start, curses.ACS_HLINE, size - 1)
        line_counter += 1
        linear_gauge(self.stdscr, offset=line_counter, size=size, start=start,
                     name='TOT',
                     value=int(swap_status.get('use', 0) / float(swap_status.get('tot', 1)) * 100.0),
                     percent=percent,
                     status='ON' if swap_status else 'OFF',
                     color=curses.color_pair(6))

    def draw(self, key):
        # Screen size
        height, width, first = self.size_page()
        # Set size chart memory
        size_x = [2, width * 1 // 2 + 5]
        size_y = [first + 1, height * 1 // 2 - 1]
        # RAM linear gauge info
        line_counter = size_y[1] + 2
        # Read RAM status and make gaugues
        ram_status = self.jetson.stats['RAM']
        lfb_status = self.jetson.stats['RAM']['lfb']
        szw, divider, unit = size_min(ram_status['tot'], start=ram_status['unit'])
        # lfb label
        percent = "{use:2.1f}{unit}/{tot:2.1f}{unit}B".format(use=ram_status['use'] / divider,
                                                              unit=unit,
                                                              tot=szw)
        label_lfb = "(lfb {nblock}x{size}{unit}B)".format(nblock=lfb_status['nblock'],
                                                          size=lfb_status['size'],
                                                          unit=lfb_status['unit'])
        # Draw the GPU chart
        self.chart_ram.draw(self.stdscr, size_x, size_y, label="{percent} - {lfb}".format(percent=percent, lfb=label_lfb))
        # Make swap list file
        self.swap_menu(lc=first, start=size_x[1] + 3, size=size_x[1] - 13, width=width)
        # Draw the Memory gague
        linear_gauge(self.stdscr, offset=line_counter, size=width,
                     name='Mem',
                     value=int(ram_status['use'] / float(ram_status['tot']) * 100.0),
                     label=label_lfb,
                     percent=percent,
                     color=curses.color_pair(6))
        # IRAM linear gauge info
        if 'IRAM' in self.jetson.stats:
            iram_status = self.jetson.stats['IRAM']
            line_counter += 1
            szw, divider, unit = size_min(iram_status['tot'], start=iram_status['unit'])
            # lfb label
            percent = "{use:2.1f}{unit}/{tot:2.1f}{unit}B".format(use=iram_status['use'] / divider,
                                                                  unit=unit,
                                                                  tot=szw)
            label_lfb = "(lfb {size}{unit}B)".format(size=iram_status['lfb']['size'],
                                                     unit=iram_status['lfb']['unit'])
            linear_gauge(self.stdscr, offset=line_counter, size=width,
                         name='Imm',
                         value=int(iram_status['use'] / float(iram_status['tot']) * 100.0),
                         label=label_lfb,
                         percent=percent,
                         color=curses.color_pair(6))
        # EMC linear gauge info
        line_counter += 1
        emc = self.jetson.stats.get('EMC', {})
        linear_gauge(self.stdscr, offset=line_counter, size=width,
                     name='EMC',
                     value=emc.get('val', 0),
                     status='ON' if emc else 'SUDO SUGGESTED',
                     label=label_freq(emc),
                     color=curses.color_pair(6))
        if self.jetson.userid == 0:
            # Clear cache button
            box_keyboard(self.stdscr, 1, first + height - 7, "c", key)
            clear_cache = "Clear cache"
            self.stdscr.addstr(first + height - 6, 7, clear_cache, curses.A_NORMAL)
        if self.jetson.userid == 0:
            # Swap controller
            box_keyboard(self.stdscr, 1, first + height - 4, "h", key)
            self.stdscr.addstr(first + height - 4, 7, "Extra", curses.A_BOLD)
            enable_swap = "Swap"
            self.stdscr.addstr(first + height - 3, 7, enable_swap, curses.A_NORMAL)
            # Status swap
            swap_enable = self.jetson.swap.enable
            enabled_box = "Enabled" if swap_enable else "Disable"
            box_status(self.stdscr, 9 + len(enable_swap), first + height - 4, enabled_box, swap_enable)
            start_pos = 10 + len(enable_swap)
            if not swap_enable:
                # Draw keys to decrease size swap
                box_keyboard(self.stdscr, start_pos + 10, first + height - 4, "-", key)
                # Draw selected number
                swp_size = int(self.jetson.swap.size)
                if swp_size > len(self.jetson.swap):
                    color = curses.color_pair(2)
                elif swp_size < len(self.jetson.swap):
                    color = curses.color_pair(3)
                else:
                    color = curses.A_NORMAL
                self.stdscr.addstr(first + height - 3, start_pos + 16, "{size: <2}".format(size=swp_size), color)
                self.stdscr.addstr(first + height - 3, start_pos + 18, "Gb", curses.A_BOLD)
                # Draw keys to increase size swap
                box_keyboard(self.stdscr, start_pos + 21, first + height - 4, "+", key)
            # else:
            #    # Print folder swapfile
            #    self.stdscr.addstr(first + height - 3, start_pos + 11, "{folder}".format(folder=self.jetson.swap.file), curses.A_BOLD)

    def keyboard(self, key):
        if self.jetson.userid == 0:
            swap_enable = self.jetson.swap.enable
            # Clear cache script
            if key == ord('c'):
                self.jetson.swap.clearCache()
            if key == ord('h'):
                # Change status swap
                self.jetson.swap.enable = operator.not_(swap_enable)
            # Enable nvpmodel control
            if not swap_enable:
                if key == ord('+'):
                    self.jetson.swap.increase()
                elif key == ord('-'):
                    self.jetson.swap.decrease()
# EOF
