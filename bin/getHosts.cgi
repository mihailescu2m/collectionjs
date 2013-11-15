#!/usr/bin/perl

# Copyright (C) 2013 Marian Mihailescu
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#   Marian Mihailescu <mihailescu2m at gmail.com>

BEGIN
{
	if (defined $ENV{'SCRIPT_FILENAME'}) {
		if ($ENV{'SCRIPT_FILENAME'} =~ m{^(/.+)/bin/[^/]+$}) {
			$::BASE_DIR = $1;
			unshift (@::INC, "$::BASE_DIR/lib");
		}
	}
}

use CGI (':cgi');
use JSON;
use Collectd::Graph::Common (qw(get_all_hosts get_plugin_selection));

sub main{
	print header('application/json');

	my @hosts = get_all_hosts ();
	my @plugins = keys get_plugin_selection ();
	@plugins = sort { $a cmp $b } @plugins;

	my $json->{"hosts"} = \@hosts;
	   $json->{"plugins"} = \@plugins;

	print to_json($json);

	return;
}

main ();

