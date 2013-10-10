#Author : Abhinav Narain
#Date : Sept 17, 2013
#Purpose : To read the binary files with data from BISmark deployment in homes
# Gives the rates used by all devices in the network where the Bismark Access Point is installed
# Gives the distribution of rates of each of the device connected to Bismark Access Point and exchanging data 
# Gives the scatterplot for the RSSI and received bitrates of the connected devices 


import os,sys,re
import gzip
import struct 
from collections import defaultdict

from  header import *
from mac_parser import * 
from utils import *
from rate import * 

from magicplott import * 
try:
    import cPickle as pickle
except ImportError:
    import pickle

rate_distribution=defaultdict(int)
def all_devices_rates_file_reader(t1,t2,data_fs):
    '''
    Fetches all the birates in a home in a data structure from file
    '''
    global damaged_frames
    file_count=0
    for data_f_n in data_fs :
        filename_list.append(data_f_n.split('-'))
        unix_time.add(int(data_f_n.split('-')[1]))
        if not (data_f_n.split('-')[2]=='d'):
            print "its not a data file ; skip "
            continue 

    filename_list.sort(key=lambda x : int(x[3]))
    filename_list.sort(key=lambda x : int(x[1]))
    tt=0
    for data_f_name_list in filename_list : #data_fs :    
        file_count=file_count+1
        data_f_name="-".join(data_f_name_list)
        data_f= gzip.open(data_f_dir+data_f_name,'rb')
        data_file_content=data_f.read()
        data_f.close()
        data_file_current_timestamp=0
        data_file_seq_n=0
        bismark_id_data_file=0
        start_64_timestamp_data_file=0
        for i in xrange(len(data_file_content )):
            if data_file_content[i]=='\n':
                bismark_data_file_header = str(data_file_content[0:i])
                ents= bismark_data_file_header.split(' ')
                bismark_id_data_file=ents[0]
                start_64_timestamp_data_file= int(ents[1])
                data_file_seq_no= int(ents[2])
                data_file_current_timestamp=int(ents[3])
                data_file_header_byte_count =i
                break

        data_contents=data_file_content.split('\n----\n')
        header_and_correct_data_frames = data_contents[0]
        err_data_frames = data_contents[1]
        correct_data_frames_missed=data_contents[2]
        err_data_frames_missed=data_contents[3]

    #done with reading the binary blobs from file ; now check for timestamps are correct
        '''
        if  (data_file_current_timestamp < t1-1):
            continue 
        if (data_file_current_timestamp >t2+1):
            break 
        '''
        correct_data_frames=header_and_correct_data_frames[data_file_header_byte_count+1:]
        data_index=0
        for idx in xrange(0,len(correct_data_frames)-DATA_STRUCT_SIZE ,DATA_STRUCT_SIZE ):	
            frame=correct_data_frames[data_index:data_index+DATA_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)        
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)  
            if success==1:
                for key in frame_elem.keys():
                    tsf=key                                    
                    parse_data_frame(frame,radiotap_len,frame_elem)
#TODO : fix the multicast and broadcast bitrates to be excluded
                    if radiotap_len ==RADIOTAP_RX_LEN :
                        rate_distribution[frame_elem[tsf][7]] +=1
                    elif radiotap_len==RADIOTAP_TX_LEN :
                        rate_distribution[frame_elem[tsf][2]] +=1
                    else :
                        print "data frame: impossible radiotap len"
            else:
                print "success denied; incorrect data frame"
                damaged_frames +=1
            data_index=data_index+DATA_STRUCT_SIZE
            del frame_elem
            del monitor_elem
        
        data_index=0
        for idx in xrange(0,len(err_data_frames)-DATA_ERR_STRUCT_SIZE,DATA_ERR_STRUCT_SIZE ):   
            frame=err_data_frames[data_index:data_index+DATA_ERR_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)
            if success==1:
                for key in frame_elem.keys():
                    tsf=key
                parse_err_data_frame(frame,radiotap_len,frame_elem)
                if radiotap_len == RADIOTAP_RX_LEN:                                    
                    rate_distribution[frame_elem[tsf][7]] +=1
                elif radiotap_len ==RADIOTAP_TX_LEN :
                    print "err tx", frame_elem
                    sys.exit(1)
                else :
                    print "impossible radiotap len detected ; Report CERN"             
            else :
                print "success denied; incorrect data frame" 
                   
            data_index= data_index+DATA_ERR_STRUCT_SIZE
            del frame_elem
            del monitor_elem    
        
        if file_count %10 == 0:
            print file_count


tx_timeseries,rx_timeseries=[],[]
def connected_devices_rates_file_reader(t1,t2,data_fs):
    '''
    Fetches the bitrate of each device from a home (uplink/downlink)
    '''
    global damaged_frames
    file_count=0
    for data_f_n in data_fs :
        filename_list.append(data_f_n.split('-'))
        unix_time.add(int(data_f_n.split('-')[1]))
        if not (data_f_n.split('-')[2]=='d'):
            print "its not a data file ; skip "
            continue 

    filename_list.sort(key=lambda x : int(x[3]))
    filename_list.sort(key=lambda x : int(x[1]))
    tt=0
    for data_f_name_list in filename_list : #data_fs :    
        file_count=file_count+1
        data_f_name="-".join(data_f_name_list)
        data_f= gzip.open(data_f_dir+data_f_name,'rb')
        data_file_content=data_f.read()
        data_f.close()
        data_file_current_timestamp=0
        data_file_seq_n=0
        bismark_id_data_file=0
        start_64_timestamp_data_file=0
        for i in xrange(len(data_file_content )):
            if data_file_content[i]=='\n':
                bismark_data_file_header = str(data_file_content[0:i])
                ents= bismark_data_file_header.split(' ')
                bismark_id_data_file=ents[0]
                start_64_timestamp_data_file= int(ents[1])
                data_file_seq_no= int(ents[2])
                data_file_current_timestamp=int(ents[3])
                data_file_header_byte_count =i
                break

        data_contents=data_file_content.split('\n----\n')
        header_and_correct_data_frames = data_contents[0]
        err_data_frames = data_contents[1]
        correct_data_frames_missed=data_contents[2]
        err_data_frames_missed=data_contents[3]

    #done with reading the binary blobs from file ; now check for timestamps are correct
        '''
        if  (data_file_current_timestamp < t1-1):
            continue 
        if (data_file_current_timestamp >t2+1):
            break 
        '''
        correct_data_frames=header_and_correct_data_frames[data_file_header_byte_count+1:]
        data_index=0
        for idx in xrange(0,len(correct_data_frames)-DATA_STRUCT_SIZE ,DATA_STRUCT_SIZE ):	
            frame=correct_data_frames[data_index:data_index+DATA_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)        
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)  
            if success==1:
                for key in frame_elem.keys():
                    tsf=key                                    
                    parse_data_frame(frame,radiotap_len,frame_elem)
                    temp=frame_elem[tsf]
                    temp.insert(0,tsf)
                    if radiotap_len ==RADIOTAP_RX_LEN :
                        rx_timeseries.append(temp)
                    elif radiotap_len==RADIOTAP_TX_LEN :
                        tx_timeseries.append(temp)
                    else :
                        print "data frame: impossible radiotap len"
            else:
                print "success denied; incorrect data frame"
                damaged_frames +=1
            data_index=data_index+DATA_STRUCT_SIZE
            del frame_elem
            del monitor_elem
        
        data_index=0

        for idx in xrange(0,len(err_data_frames)-DATA_ERR_STRUCT_SIZE,DATA_ERR_STRUCT_SIZE ):   
            frame=err_data_frames[data_index:data_index+DATA_ERR_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)
            #not sure to use the erroneous frames
            break 
            if success==1:
                for key in frame_elem.keys():
                    tsf=key
                parse_err_data_frame(frame,radiotap_len,frame_elem)
                temp=frame_elem[tsf]
                temp.insert(0,tsf)
                if radiotap_len == RADIOTAP_RX_LEN:              
                    rx_timeseries.append(temp)
                elif radiotap_len ==RADIOTAP_TX_LEN :
                    print "THIS IS err tx",frame_elem
                    sys.exit(1)
                else :
                    print "impossible radiotap len detected ; Report CERN"             
            else :
                print "success denied; incorrect data frame" 
                   
            data_index= data_index+DATA_ERR_STRUCT_SIZE
            del frame_elem
            del monitor_elem
        
        if file_count %10 == 0:
            print file_count


serialized_timeseries=[]
def connected_devices_updown_rates_file_reader(t1,t2,data_fs):
    '''
    Fetches the bitrate of each device from a home (uplink/downlink)
    '''
    global damaged_frames
    file_count=0
    for data_f_n in data_fs :
        filename_list.append(data_f_n.split('-'))
        unix_time.add(int(data_f_n.split('-')[1]))
        if not (data_f_n.split('-')[2]=='d'):
            print "its not a data file ; skip "
            continue 

    filename_list.sort(key=lambda x : int(x[3]))
    filename_list.sort(key=lambda x : int(x[1]))
    tt=0
    for data_f_name_list in filename_list : #data_fs :    
        file_count=file_count+1
        data_f_name="-".join(data_f_name_list)
        data_f= gzip.open(data_f_dir+data_f_name,'rb')
        data_file_content=data_f.read()
        data_f.close()
        data_file_current_timestamp=0
        data_file_seq_n=0
        bismark_id_data_file=0
        start_64_timestamp_data_file=0
        for i in xrange(len(data_file_content )):
            if data_file_content[i]=='\n':
                bismark_data_file_header = str(data_file_content[0:i])
                ents= bismark_data_file_header.split(' ')
                bismark_id_data_file=ents[0]
                start_64_timestamp_data_file= int(ents[1])
                data_file_seq_no= int(ents[2])
                data_file_current_timestamp=int(ents[3])
                data_file_header_byte_count =i
                break

        data_contents=data_file_content.split('\n----\n')
        header_and_correct_data_frames = data_contents[0]
        err_data_frames = data_contents[1]
        correct_data_frames_missed=data_contents[2]
        err_data_frames_missed=data_contents[3]

    #done with reading the binary blobs from file ; now check for timestamps are correct
        '''
        if  (data_file_current_timestamp < t1-1):
            continue 
        if (data_file_current_timestamp >t2+1):
            break 
        '''
        correct_data_frames=header_and_correct_data_frames[data_file_header_byte_count+1:]
        data_index=0
        for idx in xrange(0,len(correct_data_frames)-DATA_STRUCT_SIZE ,DATA_STRUCT_SIZE ):	
            frame=correct_data_frames[data_index:data_index+DATA_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)        
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)  
            if success==1:
                for key in frame_elem.keys():
                    tsf=key                                    
                    parse_data_frame(frame,radiotap_len,frame_elem)
                    temp=frame_elem[tsf]
                    temp.insert(0,tsf)
                    if radiotap_len ==RADIOTAP_RX_LEN :
                        serialized_timeseries.append(temp)
                    elif radiotap_len==RADIOTAP_TX_LEN :
                        serialized_timeseries.append(temp)
                    else :
                        print "data frame: impossible radiotap len"
            else:
                print "success denied; incorrect data frame"
                damaged_frames +=1
            data_index=data_index+DATA_STRUCT_SIZE
            del frame_elem
            del monitor_elem
        
        data_index=0

        for idx in xrange(0,len(err_data_frames)-DATA_ERR_STRUCT_SIZE,DATA_ERR_STRUCT_SIZE ):   
            frame=err_data_frames[data_index:data_index+DATA_ERR_STRUCT_SIZE]
            offset,success,tsf= 8,-1,0
            header = frame[:offset]
            frame_elem=defaultdict(list)
            monitor_elem=defaultdict(list)
            (version,pad,radiotap_len,present_flag)=struct.unpack('<BBHI',header)
            (success,frame_elem,monitor_elem)=parse_radiotap(frame,radiotap_len,present_flag,offset,monitor_elem,frame_elem)
            #not sure to use the erroneous frames
            break 
            if success==1:
                for key in frame_elem.keys():
                    tsf=key
                parse_err_data_frame(frame,radiotap_len,frame_elem)
                temp=frame_elem[tsf]
                temp.insert(0,tsf)
                if radiotap_len == RADIOTAP_RX_LEN:              
                    serialized_timeseries.append(temp)
                elif radiotap_len ==RADIOTAP_TX_LEN :
                    print "THIS IS err tx",frame_elem
                    sys.exit(1)
                else :
                    print "impossible radiotap len detected ; Report CERN"             
            else :
                print "success denied; incorrect data frame" 
                   
            data_index= data_index+DATA_ERR_STRUCT_SIZE
            del frame_elem
            del monitor_elem
        
        if file_count %10 == 0:
            print file_count




def plot_all_devices_bitrate_distribution(router_id,t1,t2,data_fs):
    '''
    Plots the distribution of bitrates occuring in the whole wireless network
    '''
#TODO : fix the multicast/broadcast bitrate to be shown with a different color in the graph
    all_devices_rates_file_reader(t1,t2,data_fs)
    if 0:
        import operator    
        max_freq= rate_distribution[max(rate_distribution.iteritems(), key=operator.itemgetter(1))[0]]
    agg=0
    for k,v in rate_distribution.iteritems():
        agg=agg+v
        
    for k,v in rate_distribution.iteritems():
        v = v*100.0/ agg
        rate_distribution[k]=v
    x_axis=rate_distribution.keys()
    x_axis.sort()
    y_axis=[]
    for i in range(0,len(x_axis)):
        y_axis.append( rate_distribution[x_axis[i]])        

    bar_graph_plotter(x_axis,
                      y_axis,
                      '802.11 bitrates',
                      'Distribution of bitrate',
                      'Overal distribution of bitrates used by all devices in a Home ('+router_id+')',
                      router_id+'_bitrate_dist_2_4.png')


def device_rate_vs_rssi_plots(t1,t2,data_fs,router_id):
    '''
    Plots the received rate (from device) and the RSSI 
    of the device.
    '''
    connected_devices_rates_file_reader(t1,t2,data_fs)
    rx_timeseries.sort(key=lambda x:x[0])
    tx_timeseries.sort(key=lambda x:x[0])
    Station_list=list(Station)
    rate_rssi_table=defaultdict(list)
    for j in range(0,len(Station_list)):
        rate_tx_hist=defaultdict(int)
        rssi_list,rates_list=[],[]
        for i in range(0,len(tx_timeseries)):
            frame = tx_timeseries[i]            
            if frame[12]==Station_list[j] :
                rate_tx_hist[frame[3]] +=1 

        for i in range(0,len(rx_timeseries)):
            frame = rx_timeseries[i]
            if frame[12]==Station_list[j] and frame[11]>0:
                rates_list.append(frame[8])                
                rssi_list.append(frame[11])
                
        rate_rssi_table[Station_list[j]].append(rates_list)
        rate_rssi_table[Station_list[j]].append(rssi_list)
    
    plotter_scatter_rssi_rate(Station_list,
                    rate_rssi_table,
                    'RSSI (dBm)',
                    'Device transmission rate',
                    'Variation of device bitrate with RSSI',
                    output_folder+router_id+'_rssi_rate.png')
    


def device_uplink_downlink_rates_plots(t1,t2,data_fs):
    '''
    Plots the histograms of bitrates used in uplink and 
    downlink directions for the devices connected with router    
    '''
    connected_devices_rates_file_reader(t1,t2,data_fs)
    rx_timeseries.sort(key=lambda x:x[0])
    tx_timeseries.sort(key=lambda x:x[0])
    Station_list=list(Station)  
    rates_hist_table=defaultdict(list)
    for j in range(0,len(Station_list)):
        rate_rx_hist=defaultdict(int)
        rate_tx_hist=defaultdict(int)
        for i in range(0,len(tx_timeseries)):
            frame = tx_timeseries[i]            
            if frame[12]==Station_list[j] :
                rate_tx_hist[frame[3]] +=1 

        for i in range(0,len(rx_timeseries)):
            frame = rx_timeseries[i]
            if frame[12]==Station_list[j] and frame[11]>0:
                rates_list.append(frame[8])                
                rate_rx_hist[frame[8]] +=1 
        s=0
        for k,v in rate_rx_hist.iteritems():
            s= s+v
        for k,v in rate_rx_hist.iteritems():
            rate_rx_hist[k]=  v*1.0/s
            
        s=0
        for k,v in rate_tx_hist.iteritems():
            s= s+v
        for k,v in rate_tx_hist.iteritems():
            rate_tx_hist[k]=  v*1.0/s
                                                        
        rates_hist_table[Station_list[j]].append(rate_rx_hist)
        rates_hist_table[Station_list[j]].append(rate_tx_hist)

    for k,bitrates_list in rates_hist_table.iteritems():
        from_device_bitrate_dict=bitrates_list[0]
        to_device_bitrate_dict=bitrates_list[1]
        x_axis_1=from_device_bitrate_dict.keys()
        y_axis_1=from_device_bitrate_dict.values()
        x_axis_2=to_device_bitrate_dict.keys()
        y_axis_2=to_device_bitrate_dict.values()
        bar_graph_plotter_distr( x_axis_1, y_axis_1, x_axis_2,y_axis_2,
                 'Bitrates in Home ('+router_id+')',
                 'Probability of bitrates ',
                 'Distribution of bitrates of frames received from Device ' +k,
                 'Distribution of bitrates of frames transmitted to Device '+k,
                 output_folder +router_id+'/'+''.join(k.split(':'))+'_rate_dist.png')


def per_station_packet_dumper(t1,t2,data_fs,outfolder_name,router_id):
    '''
    Dumps the packet captured to and from the AP to each of the stations
    connected to it in a dictionary
    '''
    Station_series=defaultdict(list)
    connected_devices_updown_rates_file_reader(t1,t2,data_fs)
    Station_list=list(Station)    
    for device_id in range(0,len(Station_list)):
        station_serialized_frames=[]
        for i in range(0,len(serialized_timeseries)):
            frame = serialized_timeseries[i]            
            if len(frame)==19 :
                if frame[12]==Station_list[device_id]:
                    station_serialized_frames.append(frame)
            else :
                if frame[12]==Station_list[device_id]:
                    station_serialized_frames.append(frame)

        Station_series[Station_list[device_id]].append(station_serialized_frames)
    pickle_object= []
    pickle_object.append(router_id)
    pickle_object.append(Station_series)
    f_d= outfolder_name+router_id+'.pickle'
    output_device = open(f_d, 'wb')
    pickle.dump(pickle_object,output_device)
    output_device.close()

def per_station_data_pickle_reader(home_packet_dump_input_folder,router_id):
    '''
    reads the packet trace into a dictionary for all stations for a home    
    '''
    data_fs=os.listdir(home_packet_dump_input_folder)
    home_packet_dump_table=defaultdict(list)
    for f_name in data_fs :
    #router_id,ap_macs,device_macs,ap_map,device_map,rate_map ; maps are of times 
        print f_name
        if f_name.split('.')[0]==router_id :
           _f_content= pickle.load(open(home_packet_dump_input_folder+f_name,'rb'))
           if not (router_id==_f_content[0]):
               print "there is a problem in router id... exit" 
               sys.exit(1)
           home_packet_dump_map=_f_content[1]
           return home_packet_dump_map

    print "The routerId is not in folder" 

def bitrate_scatter_plot():
    '''
    The function plots the bitrate scatter plot for upstream and downstream 
    plots
    '''
#TODO : This function is incomplete and needs to be coded !!!
    #Alex asked to :remove cases with retransmission
#    if len(packet_array[i][1])== 4 : # received frame  8 is the bitrate
#    elif len(packet_array[i][0])== 5 : #transmitted frame 3 is bitrate

if __name__=='__main__':
    if len(sys.argv) !=6 :
	print len(sys.argv)
	print "Usage : python rate_distribution.py data/<data.gz> <router_id> <t1> <t2> <outputfolder> "
	sys.exit(1)

    data_f_dir=sys.argv[1]
    router_id= sys.argv[2]
    time1 =sys.argv[3]
    time2 =sys.argv[4]
    _folder=sys.argv[5]
    data_fs=os.listdir(data_f_dir)
    [t1,t2] = timeStamp_Conversion(time1,time2,router_id)
    data_file_header_byte_count=0
    filename_list=[]
    damaged_frames=0
    unix_time=set()
    #os.system('mkdir -p '+output_folder+router_id )
    print "now processing the files to calculate time "
    #For overall rate distribution of entire home 
    #plot_all_devices_bitrate_distribution(router_id,t1,t2,data_fs)
    #For scatterplot of RSSI vs bitrate and histogram of transmitted to received bitrates    
    #device_rate_vs_rssi_plots(t1,t2,data_fs,router_id)
    #per_station_packet_dumper(t1,t2,data_fs,_folder,router_id)
    bitrate_scatter_plot(t1,t2,data_fs)
    home_packet_dump_map=per_station_data_pickle_reader(_folder,router_id)
