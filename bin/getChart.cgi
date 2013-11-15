#!/usr/bin/perl

# Copyright (C) 2008-2011  Florian Forster
# Copyright (C) 2011       noris network AG
# Copyright (C) 2013       Marian Mihailescu
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
#   Florian "octo" Forster <octo at collectd.org>
#   Marian Mihailescu <mihailescu2m at gmail.com>

use strict;
use warnings;
use utf8;
use vars (qw($BASE_DIR));

use CGI qw(:standard);
use JSON;

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

use Carp (qw(confess cluck));
use CGI (':cgi');
use RRDs ();
use File::Temp (':POSIX');

use Collectd::Graph::Config (qw(gc_read_config gc_get_scalar));
use Collectd::Graph::TypeLoader (qw(tl_load_type));

use Collectd::Graph::Common (qw(sanitize_type get_selected_files
      epoch_to_rfc1123 flush_files));
use Collectd::Graph::Type ();

sub base_dir
{
  if (defined $::BASE_DIR)
  {
    return ($::BASE_DIR);
  }

  if (!defined ($ENV{'SCRIPT_FILENAME'}))
  {
    return;
  }

  if ($ENV{'SCRIPT_FILENAME'} =~ m{^(/.+)/bin/[^/]+$})
  {
    $::BASE_DIR = $1;
    return ($::BASE_DIR);
  }

  return;
}

sub lib_dir
{
  my $base = base_dir ();

  if ($base)
  {
    return "$base/lib";
  }
  else
  {
    return "../lib";
  }
}

sub sysconf_dir
{
  my $base = base_dir ();

  if ($base)
  {
    return "$base/etc";
  }
  else
  {
    return "../etc";
  }
}

sub init
{
  my $lib_dir = lib_dir ();
  my $sysconf_dir = sysconf_dir ();

  if (!grep { $lib_dir eq $_ } (@::INC))
  {
    unshift (@::INC, $lib_dir);
  }

  gc_read_config ("$sysconf_dir/collection.conf");
}

sub main
{
  my $Begin = param ('begin');
  my $End = param ('end');
  my $Index = param ('index') || 0;
  my $ContentType = 'application/json';

  init ();

  if (param ('debug'))
  {
    print <<HTTP;
Content-Type: text/plain

HTTP
    $ContentType = 'text/plain';
  }

  { # Sanitize begin and end times
    $End ||= 0;
    $Begin ||= 0;

    if ($End =~ m/\D/)
    {
      $End = 0;
    }

    if (!$Begin || !($Begin =~ m/^-?([1-9][0-9]*)$/))
    {
      $Begin = -86400;
    }

    if ($Begin < 0)
    {
      if ($End)
      {
        $Begin = $End + $Begin;
      }
      else
      {
        $Begin = time () + $Begin;
      }
    }

    if ($Begin < 0)
    {
      $Begin = time () - 86400;
    }

    if (($End > 0) && ($Begin > $End))
    {
      my $temp = $End;
      $End = $Begin;
      $Begin = $temp;
    }
  }

  my $type = param ('type') or die;
  my $obj;

  $obj = tl_load_type ($type);
  if (!$obj)
  {
    confess ("tl_load_type ($type) failed");
  }

  $type = ucfirst (lc ($type));
  $type =~ s/_([A-Za-z])/\U$1\E/g;
  $type = sanitize_type ($type);

  my $files = get_selected_files ();
  if (param ('debug'))
  {
    require Data::Dumper;
    print Data::Dumper->Dump ([$files], ['files']);
  }
  for (@$files)
  {
    $obj->addFiles ($_);
  }

  my $expires = time ();
# IF (End is `now')
#    OR (Begin is before `now' AND End is after `now')
  if (($End == 0) || (($Begin <= $expires) && ($End >= $expires)))
  {
    # 400 == width in pixels
    my $timespan;

    if ($End == 0)
    {
      $timespan = $expires - $Begin;
    }
    else
    {
      $timespan = $End - $Begin;
    }
    $expires += int ($timespan / 400.0);
  }
# IF (End is not `now')
#    AND (End is before `now')
# ==> Graph will never change again!
  elsif (($End > 0) && ($End < $expires))
  {
    $expires += (366 * 86400);
  }
  elsif ($Begin > $expires)
  {
    $expires = $Begin;
  }

# Send FLUSH command to the daemon if necessary and possible.
  flush_files ($files,
    begin => $Begin,
    end => $End,
    addr => gc_get_scalar ('UnixSockAddr', undef),
    interval => gc_get_scalar ('Interval', 10));

  print header (-Content_type => $ContentType,
    -Last_Modified => epoch_to_rfc1123 ($obj->getLastModified ()),
    -Expires => epoch_to_rfc1123 ($expires));

  if (param ('debug'))
  {
    print "\$expires = $expires;\n";
  }

  my $args = $obj->getRRDArgs (0 + $Index);
  if (param ('debug'))
  {
    require Data::Dumper;
    print Data::Dumper->Dump ([$obj], ['obj']);
    print join (",\n", @$args) . "\n";
    print "Last-Modified: " . epoch_to_rfc1123 ($obj->getLastModified ()) . "\n";
  }
  else
  {
    my @timesel = ();
    my $status;

    if ($End) # $Begin is always true
    {
      @timesel = ('-s', $Begin, '-e', $End);
    }
    else
    {
      @timesel = ('-s', $Begin); # End is implicitely `now'.
    }

    if (-S "/var/run/rrdcached.sock" && -w "/var/run/rrdcached.sock")
    {
      $ENV{"RRDCACHED_ADDRESS"} = "/var/run/rrdcached.sock";
    }

    # now we modify the arguments for export
    my @xargs = ();
    my @series = ();
    my $t = -1;
    my $v = -1;
    my $idx = -1;
    my $sid = 0;
    foreach (@$args) {
	$idx ++;
	my @elements = split(":", $_);
	if ($elements[0] eq "-t") {
	    $t = $idx + 1;
	    next;
	}
	if ($elements[0] eq "-v") {
	    $v = $idx + 1;
	    next;
	}
	if (($elements[0] eq "DEF") || ($elements[0] eq "CDEF") || ($elements[0] eq "VDEF")) {
	    push(@xargs, $_);
	    next;
	}
	if ((index($elements[0], "LINE") != -1) || ($elements[0] eq "AREA")) {
	    my $serie = substr($elements[1], 0, index($elements[1], "#"));
	    my $name = $elements[2];
	    my $type = ($elements[0] eq "AREA") ? "area" : "line";
	    my $color = substr($elements[1], index($elements[1], "#"));
	    push(@xargs, "XPORT:" . $serie);
	    my @data = ();
	    push(@series, {sid => $sid, name => $name, type => $type, color => $color, showInLegend => (defined $name) ? 1 : 0, data => \@data});
	    $sid ++;
	}
    }

    my %title = ();
    if ($t > 0) {
	$title{text} = @$args[$t];
    }
    my %yAxis = ();
    if ($v > 0) {
	$yAxis{title} = {text => @$args[$v]};
    }

    my @result = RRDs::xport (@timesel, @xargs);
    if (my $err = RRDs::error ())
    {
      print STDERR "RRDs::xport failed: $err\n";
      exit (1);
    }

    my $start = $result[0];
    my $step = $result[2];
    for (my $serie=0; $serie < $result[3]; $serie++) {
	$series[$serie]{pointStart} = $start * 1000;
	$series[$serie]{pointInterval} = $step * 1000;
    }

    foreach (@{$result[5]}) {
	my @time = @{$_};
	for (my $serie=0; $serie < $result[3]; $serie++) {
	    my $s = $series[$serie];
	    push(@{$series[$serie]{"data"}}, $time[$serie]);
	}
    }

    my $json = new JSON;
    print $json->encode({title => \%title, yAxis => \%yAxis, series => \@series});

  }
} # sub main

main ();

# vim: set shiftwidth=2 softtabstop=2 tabstop=8 :
