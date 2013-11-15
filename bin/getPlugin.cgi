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
  if (defined $ENV{'SCRIPT_FILENAME'})
  {
    if ($ENV{'SCRIPT_FILENAME'} =~ m{^(/.+)/bin/[^/]+$})
    {
      $::BASE_DIR = $1;
      unshift (@::INC, "$::BASE_DIR/lib");
    }
  }
}

use CGI (':cgi');
use JSON;

use Collectd::Graph::Common (qw(get_selected_files));

sub main
{
	print header('application/json');

	my $hostname = param ('hostname') || '';
	my $plugin = param ('plugin') || '';

	my $selected_files = get_selected_files ();
	my @files = @$selected_files;
	my @response = ();
	my $index = 0;
	while ($index <= $#files) {
		my $value = $files[$index];
		my %hash = %$value;
		if ($hash{"hostname"} eq $hostname and $hash{"plugin"} eq $plugin) {
			my $ok = 1;
			my $i = 0;
			while ($i <= $#response) {
				my $v = $response[$i];
				my %h = %$v;
				# ignore type_instance when plugin_instance and type are the same
				# this is because we don't want a graph for each value in the RRD
				# it has the side effect of sometimes ignoring 1-value graphs with different type_instance
				# like for example cpufreq plugin, there will only be one result, for CPU0
				if ($hash{"plugin_instance"} eq $h{"plugin_instance"} and $hash{"type"} eq $h{"type"}) {
					$ok = 0;
					$v->{"ignore_type_instance"} = "yes";
				}
				$i++;
			}
			if ($ok == 1) {
				push @response, $value;
			}
		}
		$index++;
	}

	@response = sort { $a->{'plugin'} cmp $b->{'plugin'} || $a->{'plugin_instance'} cmp $b->{'plugin_instance'} || $a->{'type_instance'} cmp $b->{'type_instance'} } @response;

	my $json->{"charts"} = \@response;
    print to_json($json);

	return;
}

main ();

