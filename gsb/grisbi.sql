-- MySQL dump 10.13  Distrib 5.5.9, for Linux (i686)
--
-- Host: localhost    Database: grisbi
-- ------------------------------------------------------
-- Server version	5.5.9-log
 CREATE DATABASE `grisbi` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
use grisbi;
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_425ae3c4` (`group_id`),
  KEY `auth_group_permissions_1e014c8f` (`permission_id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_403f60f` (`user_id`),
  CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_1bb8f392` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can add group',2,'add_group'),(5,'Can change group',2,'change_group'),(6,'Can delete group',2,'delete_group'),(7,'Can add user',3,'add_user'),(8,'Can change user',3,'change_user'),(9,'Can delete user',3,'delete_user'),(10,'Can add message',4,'add_message'),(11,'Can change message',4,'change_message'),(12,'Can delete message',4,'delete_message'),(13,'Can add content type',5,'add_contenttype'),(14,'Can change content type',5,'change_contenttype'),(15,'Can delete content type',5,'delete_contenttype'),(16,'Can add session',6,'add_session'),(17,'Can change session',6,'change_session'),(18,'Can delete session',6,'delete_session'),(19,'Can add site',7,'add_site'),(20,'Can change site',7,'change_site'),(21,'Can delete site',7,'delete_site'),(22,'Can add log entry',8,'add_logentry'),(23,'Can change log entry',8,'change_logentry'),(24,'Can delete log entry',8,'delete_logentry'),(25,'Can add tiers',9,'add_tiers'),(26,'Can change tiers',9,'change_tiers'),(27,'Can delete tiers',9,'delete_tiers'),(28,'Can add devise',10,'add_devise'),(29,'Can change devise',10,'change_devise'),(30,'Can delete devise',10,'delete_devise'),(31,'Can add titre',11,'add_titre'),(32,'Can change titre',11,'change_titre'),(33,'Can delete titre',11,'delete_titre'),(34,'Can add cours',12,'add_cours'),(35,'Can change cours',12,'change_cours'),(36,'Can delete cours',12,'delete_cours'),(37,'Can add banque',13,'add_banque'),(38,'Can change banque',13,'change_banque'),(39,'Can delete banque',13,'delete_banque'),(40,'Can add catégorie',14,'add_cat'),(41,'Can change catégorie',14,'change_cat'),(42,'Can delete catégorie',14,'delete_cat'),(43,'Can add sous-catégorie',15,'add_scat'),(44,'Can change sous-catégorie',15,'change_scat'),(45,'Can delete sous-catégorie',15,'delete_scat'),(46,'Can add imputation budgétaire',16,'add_ib'),(47,'Can change imputation budgétaire',16,'change_ib'),(48,'Can delete imputation budgétaire',16,'delete_ib'),(49,'Can add sous-imputation budgétaire',17,'add_sib'),(50,'Can change sous-imputation budgétaire',17,'change_sib'),(51,'Can delete sous-imputation budgétaire',17,'delete_sib'),(52,'Can add exercice',18,'add_exercice'),(53,'Can change exercice',18,'change_exercice'),(54,'Can delete exercice',18,'delete_exercice'),(55,'Can add compte',19,'add_compte'),(56,'Can change compte',19,'change_compte'),(57,'Can delete compte',19,'delete_compte'),(58,'Can add moyen',20,'add_moyen'),(59,'Can change moyen',20,'change_moyen'),(60,'Can delete moyen',20,'delete_moyen'),(61,'Can add rapprochement',21,'add_rapp'),(62,'Can change rapprochement',21,'change_rapp'),(63,'Can delete rapprochement',21,'delete_rapp'),(64,'Can add Echéances',22,'add_echeance'),(65,'Can change Echéances',22,'change_echeance'),(66,'Can delete Echéances',22,'delete_echeance'),(67,'Can add généralités',23,'add_generalite'),(68,'Can change généralités',23,'change_generalite'),(69,'Can delete généralités',23,'delete_generalite'),(70,'Can add opération',24,'add_ope'),(71,'Can change opération',24,'change_ope'),(72,'Can delete opération',24,'delete_ope');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','','','toto@toto.com','sha1$2e0b7$ec51fbcbd32dc6a44f145f01e1dad471e6d43274',1,1,1,'2011-03-06 21:53:31','2011-03-06 21:53:31');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_403f60f` (`user_id`),
  KEY `auth_user_groups_425ae3c4` (`group_id`),
  CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_403f60f` (`user_id`),
  KEY `auth_user_user_permissions_1e014c8f` (`permission_id`),
  CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `banque`
--

DROP TABLE IF EXISTS `banque`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `banque` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cib` varchar(15) NOT NULL,
  `nom` varchar(120) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `banque`
--

LOCK TABLES `banque` WRITE;
/*!40000 ALTER TABLE `banque` DISABLE KEYS */;
/*!40000 ALTER TABLE `banque` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cat`
--

DROP TABLE IF EXISTS `cat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `typecat` varchar(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cat`
--

LOCK TABLES `cat` WRITE;
/*!40000 ALTER TABLE `cat` DISABLE KEYS */;
/*!40000 ALTER TABLE `cat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compte`
--

DROP TABLE IF EXISTS `compte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `compte` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `titulaire` varchar(120) NOT NULL,
  `type` varchar(24) NOT NULL,
  `devise_id` int(11) NOT NULL,
  `banque_id` int(11) DEFAULT NULL,
  `guichet` varchar(15) NOT NULL,
  `num_compte` varchar(60) NOT NULL,
  `cle_compte` bigint(20) DEFAULT NULL,
  `solde_init` double NOT NULL,
  `solde_mini_voulu` double DEFAULT NULL,
  `solde_mini_autorise` double DEFAULT NULL,
  `date_dernier_releve` date DEFAULT NULL,
  `solde_dernier_releve` double DEFAULT NULL,
  `cloture` tinyint(1) NOT NULL,
  `nb_lignes_ope` bigint(20) DEFAULT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `compte_536f7620` (`devise_id`),
  KEY `compte_2134032c` (`banque_id`),
  CONSTRAINT `devise_id_refs_id_821808f` FOREIGN KEY (`devise_id`) REFERENCES `devise` (`id`),
  CONSTRAINT `banque_id_refs_id_19be1a53` FOREIGN KEY (`banque_id`) REFERENCES `banque` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compte`
--

LOCK TABLES `compte` WRITE;
/*!40000 ALTER TABLE `compte` DISABLE KEYS */;
/*!40000 ALTER TABLE `compte` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cours`
--

DROP TABLE IF EXISTS `cours`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cours` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `valeur` double NOT NULL,
  `isin` bigint(20) NOT NULL,
  `date_cours` date NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `isin` (`isin`,`date_cours`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cours`
--

LOCK TABLES `cours` WRITE;
/*!40000 ALTER TABLE `cours` DISABLE KEYS */;
/*!40000 ALTER TABLE `cours` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devise`
--

DROP TABLE IF EXISTS `devise`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `devise` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `dernier_tx_de_change` double NOT NULL,
  `date_dernier_change` date NOT NULL,
  `isocode` varchar(3) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `isocode` (`isocode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devise`
--

LOCK TABLES `devise` WRITE;
/*!40000 ALTER TABLE `devise` DISABLE KEYS */;
/*!40000 ALTER TABLE `devise` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_403f60f` (`user_id`),
  KEY `django_admin_log_1bb8f392` (`content_type_id`),
  CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'permission','auth','permission'),(2,'group','auth','group'),(3,'user','auth','user'),(4,'message','auth','message'),(5,'content type','contenttypes','contenttype'),(6,'session','sessions','session'),(7,'site','sites','site'),(8,'log entry','admin','logentry'),(9,'tiers','gsb','tiers'),(10,'devise','gsb','devise'),(11,'titre','gsb','titre'),(12,'cours','gsb','cours'),(13,'banque','gsb','banque'),(14,'catégorie','gsb','cat'),(15,'sous-catégorie','gsb','scat'),(16,'imputation budgétaire','gsb','ib'),(17,'sous-imputation budgétaire','gsb','sib'),(18,'exercice','gsb','exercice'),(19,'compte','gsb','compte'),(20,'moyen','gsb','moyen'),(21,'rapprochement','gsb','rapp'),(22,'Echéances','gsb','echeance'),(23,'généralités','gsb','generalite'),(24,'opération','gsb','ope');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'example.com','example.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `echeance`
--

DROP TABLE IF EXISTS `echeance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `echeance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_ech` date NOT NULL,
  `compte_id` int(11) NOT NULL,
  `montant` double NOT NULL,
  `devise_id` int(11) NOT NULL,
  `tiers_id` int(11) NOT NULL,
  `Cat_id` int(11) DEFAULT NULL,
  `Scat_id` int(11) DEFAULT NULL,
  `compte_virement_id` int(11) DEFAULT NULL,
  `moyen_id` int(11) DEFAULT NULL,
  `moyen_virement_id` int(11) DEFAULT NULL,
  `Exercice_id` int(11) DEFAULT NULL,
  `ib_id` int(11) DEFAULT NULL,
  `sib_id` int(11) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `inscription_automatique` tinyint(1) NOT NULL,
  `periodicite` longtext NOT NULL,
  `intervalle` bigint(20) NOT NULL,
  `periode_perso` longtext NOT NULL,
  `date_limite` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `echeance_28431022` (`compte_id`),
  KEY `echeance_536f7620` (`devise_id`),
  KEY `echeance_464b9a12` (`tiers_id`),
  KEY `echeance_6b360bf1` (`Cat_id`),
  KEY `echeance_62fa57b9` (`Scat_id`),
  KEY `echeance_14e4360c` (`compte_virement_id`),
  KEY `echeance_2cdaa15f` (`moyen_id`),
  KEY `echeance_63d61255` (`moyen_virement_id`),
  KEY `echeance_77a4b192` (`Exercice_id`),
  KEY `echeance_33f970d3` (`ib_id`),
  KEY `echeance_118cb321` (`sib_id`),
  CONSTRAINT `Exercice_id_refs_id_57093b2b` FOREIGN KEY (`Exercice_id`) REFERENCES `exercice` (`id`),
  CONSTRAINT `Cat_id_refs_id_545aab52` FOREIGN KEY (`Cat_id`) REFERENCES `cat` (`id`),
  CONSTRAINT `compte_id_refs_id_3509d599` FOREIGN KEY (`compte_id`) REFERENCES `compte` (`id`),
  CONSTRAINT `compte_virement_id_refs_id_3509d599` FOREIGN KEY (`compte_virement_id`) REFERENCES `compte` (`id`),
  CONSTRAINT `devise_id_refs_id_3f6079b1` FOREIGN KEY (`devise_id`) REFERENCES `devise` (`id`),
  CONSTRAINT `ib_id_refs_id_6df59ff6` FOREIGN KEY (`ib_id`) REFERENCES `ib` (`id`),
  CONSTRAINT `moyen_id_refs_id_288e7884` FOREIGN KEY (`moyen_id`) REFERENCES `moyen` (`id`),
  CONSTRAINT `moyen_virement_id_refs_id_288e7884` FOREIGN KEY (`moyen_virement_id`) REFERENCES `moyen` (`id`),
  CONSTRAINT `Scat_id_refs_id_33c2ffb8` FOREIGN KEY (`Scat_id`) REFERENCES `scat` (`id`),
  CONSTRAINT `sib_id_refs_id_e3dec04` FOREIGN KEY (`sib_id`) REFERENCES `sib` (`id`),
  CONSTRAINT `tiers_id_refs_id_8a79091` FOREIGN KEY (`tiers_id`) REFERENCES `tiers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `echeance`
--

LOCK TABLES `echeance` WRITE;
/*!40000 ALTER TABLE `echeance` DISABLE KEYS */;
/*!40000 ALTER TABLE `echeance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercice`
--

DROP TABLE IF EXISTS `exercice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exercice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `nom` varchar(120) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercice`
--

LOCK TABLES `exercice` WRITE;
/*!40000 ALTER TABLE `exercice` DISABLE KEYS */;
/*!40000 ALTER TABLE `exercice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `generalite`
--

DROP TABLE IF EXISTS `generalite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `generalite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `titre` varchar(120) NOT NULL,
  `utilise_exercices` tinyint(1) NOT NULL,
  `utilise_ib` tinyint(1) NOT NULL,
  `utilise_pc` tinyint(1) NOT NULL,
  `devise_generale_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `generalite_499589c1` (`devise_generale_id`),
  CONSTRAINT `devise_generale_id_refs_id_725764b1` FOREIGN KEY (`devise_generale_id`) REFERENCES `devise` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `generalite`
--

LOCK TABLES `generalite` WRITE;
/*!40000 ALTER TABLE `generalite` DISABLE KEYS */;
/*!40000 ALTER TABLE `generalite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ib`
--

DROP TABLE IF EXISTS `ib`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ib` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `typeimp` varchar(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ib`
--

LOCK TABLES `ib` WRITE;
/*!40000 ALTER TABLE `ib` DISABLE KEYS */;
/*!40000 ALTER TABLE `ib` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `moyen`
--

DROP TABLE IF EXISTS `moyen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `moyen` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `compte_id` int(11) NOT NULL,
  `nom` varchar(120) NOT NULL,
  `signe` varchar(1) NOT NULL,
  `affiche_numero` tinyint(1) NOT NULL,
  `num_auto` tinyint(1) NOT NULL,
  `num_en_cours` bigint(20) DEFAULT NULL,
  `grisbi_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `compte_id` (`compte_id`,`grisbi_id`),
  KEY `moyen_28431022` (`compte_id`),
  CONSTRAINT `compte_id_refs_id_546a7a30` FOREIGN KEY (`compte_id`) REFERENCES `compte` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `moyen`
--

LOCK TABLES `moyen` WRITE;
/*!40000 ALTER TABLE `moyen` DISABLE KEYS */;
/*!40000 ALTER TABLE `moyen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ope`
--

DROP TABLE IF EXISTS `ope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ope` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `compte_id` int(11) NOT NULL,
  `date` date NOT NULL,
  `date_val` date DEFAULT NULL,
  `montant` double NOT NULL,
  `devise_id` int(11) NOT NULL,
  `tiers_id` int(11) DEFAULT NULL,
  `Cat_id` int(11) DEFAULT NULL,
  `Scat_id` int(11) DEFAULT NULL,
  `is_mere` tinyint(1) NOT NULL,
  `notes` longtext NOT NULL,
  `Moyen_id` int(11) DEFAULT NULL,
  `numcheque` varchar(120) NOT NULL,
  `pointe` varchar(2) NOT NULL,
  `rapp_id` int(11) DEFAULT NULL,
  `Exercice_id` int(11) DEFAULT NULL,
  `ib_id` int(11) DEFAULT NULL,
  `sib_id` int(11) DEFAULT NULL,
  `jumelle_id` int(11) DEFAULT NULL,
  `mere_id` int(11) DEFAULT NULL,
  `_order` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ope_28431022` (`compte_id`),
  KEY `ope_536f7620` (`devise_id`),
  KEY `ope_464b9a12` (`tiers_id`),
  KEY `ope_6b360bf1` (`Cat_id`),
  KEY `ope_62fa57b9` (`Scat_id`),
  KEY `ope_9f2a97f` (`Moyen_id`),
  KEY `ope_1a39db13` (`rapp_id`),
  KEY `ope_77a4b192` (`Exercice_id`),
  KEY `ope_33f970d3` (`ib_id`),
  KEY `ope_118cb321` (`sib_id`),
  KEY `ope_c7593d1` (`jumelle_id`),
  KEY `ope_26fec3d9` (`mere_id`),
  CONSTRAINT `Exercice_id_refs_id_7ba5b0bc` FOREIGN KEY (`Exercice_id`) REFERENCES `exercice` (`id`),
  CONSTRAINT `Cat_id_refs_id_1aec001` FOREIGN KEY (`Cat_id`) REFERENCES `cat` (`id`),
  CONSTRAINT `compte_id_refs_id_3e2b7cf8` FOREIGN KEY (`compte_id`) REFERENCES `compte` (`id`),
  CONSTRAINT `devise_id_refs_id_5e8710be` FOREIGN KEY (`devise_id`) REFERENCES `devise` (`id`),
  CONSTRAINT `ib_id_refs_id_6d17159b` FOREIGN KEY (`ib_id`) REFERENCES `ib` (`id`),
  CONSTRAINT `jumelle_id_refs_id_1366567d` FOREIGN KEY (`jumelle_id`) REFERENCES `ope` (`id`),
  CONSTRAINT `mere_id_refs_id_1366567d` FOREIGN KEY (`mere_id`) REFERENCES `ope` (`id`),
  CONSTRAINT `Moyen_id_refs_id_17612e15` FOREIGN KEY (`Moyen_id`) REFERENCES `moyen` (`id`),
  CONSTRAINT `rapp_id_refs_id_1b895b6b` FOREIGN KEY (`rapp_id`) REFERENCES `rapp` (`id`),
  CONSTRAINT `Scat_id_refs_id_41283549` FOREIGN KEY (`Scat_id`) REFERENCES `scat` (`id`),
  CONSTRAINT `sib_id_refs_id_1a8cd3e3` FOREIGN KEY (`sib_id`) REFERENCES `sib` (`id`),
  CONSTRAINT `tiers_id_refs_id_76827870` FOREIGN KEY (`tiers_id`) REFERENCES `tiers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ope`
--

LOCK TABLES `ope` WRITE;
/*!40000 ALTER TABLE `ope` DISABLE KEYS */;
/*!40000 ALTER TABLE `ope` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rapp`
--

DROP TABLE IF EXISTS `rapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rapp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `date` date NOT NULL,
  `compte_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `rapp_28431022` (`compte_id`),
  CONSTRAINT `compte_id_refs_id_7debd492` FOREIGN KEY (`compte_id`) REFERENCES `compte` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rapp`
--

LOCK TABLES `rapp` WRITE;
/*!40000 ALTER TABLE `rapp` DISABLE KEYS */;
/*!40000 ALTER TABLE `rapp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scat`
--

DROP TABLE IF EXISTS `scat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cat_id` int(11) NOT NULL,
  `nom` varchar(120) NOT NULL,
  `grisbi_id` bigint(20) NOT NULL,
  `_order` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cat_id` (`cat_id`,`grisbi_id`),
  KEY `scat_5120efd1` (`cat_id`),
  CONSTRAINT `cat_id_refs_id_2a82d27b` FOREIGN KEY (`cat_id`) REFERENCES `cat` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scat`
--

LOCK TABLES `scat` WRITE;
/*!40000 ALTER TABLE `scat` DISABLE KEYS */;
/*!40000 ALTER TABLE `scat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sib`
--

DROP TABLE IF EXISTS `sib`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sib` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `grisbi_id` bigint(20) NOT NULL,
  `ib_id` int(11) NOT NULL,
  `_order` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ib_id` (`ib_id`,`grisbi_id`),
  KEY `sib_33f970d3` (`ib_id`),
  CONSTRAINT `ib_id_refs_id_7417afb` FOREIGN KEY (`ib_id`) REFERENCES `ib` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sib`
--

LOCK TABLES `sib` WRITE;
/*!40000 ALTER TABLE `sib` DISABLE KEYS */;
/*!40000 ALTER TABLE `sib` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tiers`
--

DROP TABLE IF EXISTS `tiers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tiers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(120) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tiers`
--

LOCK TABLES `tiers` WRITE;
/*!40000 ALTER TABLE `tiers` DISABLE KEYS */;
/*!40000 ALTER TABLE `tiers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `titre`
--

DROP TABLE IF EXISTS `titre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `titre` (
  `nom` varchar(120) NOT NULL,
  `isin` varchar(60) NOT NULL,
  `tiers_id` int(11) NOT NULL,
  `type` varchar(60) NOT NULL,
  PRIMARY KEY (`isin`),
  KEY `titre_464b9a12` (`tiers_id`),
  CONSTRAINT `tiers_id_refs_id_51c0e578` FOREIGN KEY (`tiers_id`) REFERENCES `tiers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `titre`
--

LOCK TABLES `titre` WRITE;
/*!40000 ALTER TABLE `titre` DISABLE KEYS */;
/*!40000 ALTER TABLE `titre` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-03-06 22:54:01
